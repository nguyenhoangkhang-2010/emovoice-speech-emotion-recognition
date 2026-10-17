# Baseline Random Forest chạy thêm để so sánh (không thay thế mô hình chính): nạp pickle, dự đoán từ 212 đặc trưng, tìm trong bảng models, hiện ở trang kết quả.
from contextlib import contextmanager

import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401  (đăng ký bảng vào Base.metadata)
from core.session import SessionUser
from db.base import Base
from ml import baseline, preprocess
from ml.config import EMOTION_NAMES
from services import baseline_service, model_service
from ui import render
from ui.pages import analyze

joblib = pytest.importorskip("joblib")
sf = pytest.importorskip("soundfile")
RandomForestClassifier = pytest.importorskip("sklearn.ensemble").RandomForestClassifier


@pytest.fixture()
def rf_file(tmp_path):
    """Random Forest nhỏ huấn luyện trên dữ liệu ngẫu nhiên, chỉ thấy 3 trong 8 nhãn (1, 4, 6) để kiểm tra việc ánh xạ nhãn."""
    rng = np.random.default_rng(0)
    x = rng.normal(size=(60, 212)).astype(np.float32)
    y = np.array([1, 4, 6] * 20)
    x[y == 4] += 2.0  # nhãn 4 tách được khỏi các nhãn còn lại
    model = RandomForestClassifier(n_estimators=10, random_state=0, n_jobs=-1).fit(x, y)
    path = tmp_path / "rf.pkl"
    joblib.dump(model, path)
    return str(path), x, y


@pytest.fixture(autouse=True)
def _clear_cache():
    baseline._cache.update(path=None, model=None)


def _wav(path, seconds=1.5):
    t = np.arange(int(seconds * 16000)) / 16000
    sf.write(str(path), (0.3 * np.sin(2 * np.pi * 220 * t)).astype(np.float32), 16000)
    return str(path)


# ---------- ml.baseline ----------
def test_probs_map_model_classes_to_system_labels(rf_file):
    path, x, y = rf_file
    probs = baseline.predict_probs(x[y == 4][0], path)
    assert probs.shape == (8,) and probs.sum() == pytest.approx(1.0)
    assert int(np.argmax(probs)) == 4  # nhãn 4 của mô hình = nhãn 4 (angry) của hệ thống
    assert all(probs[i] == 0 for i in (0, 2, 3, 5, 7))  # nhãn mô hình chưa từng thấy có xác suất 0


def test_model_is_loaded_once_and_forced_single_thread(rf_file):
    path, x, _ = rf_file
    baseline.predict_probs(x[0], path)
    first = baseline._cache["model"]
    baseline.predict_probs(x[1], path)
    assert baseline._cache["model"] is first and first.n_jobs == 1


def test_wrong_feature_count_is_rejected(tmp_path):
    model = RandomForestClassifier(n_estimators=3, random_state=0).fit(np.random.default_rng(1).normal(size=(20, 10)), [0, 1] * 10)
    path = tmp_path / "small.pkl"
    joblib.dump(model, path)
    with pytest.raises(ValueError, match="212"):
        baseline.load_random_forest(str(path))


def test_features_212_for_file_matches_training_pipeline(tmp_path):
    path = _wav(tmp_path / "a.wav")
    feats = preprocess.features_212_for_file(path)
    assert feats.shape == (212,) and feats.dtype == np.float32 and np.isfinite(feats).all()
    clean = preprocess.load_and_preprocess_audio(path)
    assert np.allclose(feats, preprocess.extract_212_features(clean))  # đúng đường tính của lúc huấn luyện: trên đoạn đã cắt lặng, không đệm 3 s


# ---------- tìm trong bảng models ----------
@pytest.fixture()
def registry(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False)

    @contextmanager
    def fake():
        s = factory()
        try:
            yield s
        finally:
            s.close()

    monkeypatch.setattr(model_service, "get_session", fake)
    return fake


def _register(name, family, checkpoint, activate=False, inference=True):
    details = {"inference": inference, "confusion": {"labels": []}}
    if family:
        details["family"] = family
    return model_service.register_model(
        name=name, model_type="T", checkpoint_path=checkpoint, accuracy=51.11, f1_score=46.39, size_mb=1.0, inference_time=1.0,
        params_total=None, params_trainable=None, eval_dataset="d", eval_samples=180, latency_device="cpu", details=details, activate=activate,
    )


def test_baseline_model_finds_only_registered_baseline_of_that_family(registry):
    assert model_service.baseline_model("random_forest") is None
    _register("Chính", None, "/m.pt", activate=True)
    assert model_service.baseline_model("random_forest") is None  # mô hình chính không phải baseline
    _register("Random Forest", "random_forest", "/rf.pkl", inference=False)
    found = model_service.baseline_model("random_forest")
    assert found["name"] == "Random Forest" and found["checkpoint_path"] == "/rf.pkl" and found["can_infer"] is False
    assert model_service.baseline_model("xgboost") is None
    assert model_service.active_model()["name"] == "Chính"  # đăng ký baseline không làm đổi mô hình đang dùng


# ---------- baseline_service ----------
def test_run_random_forest_returns_probs_and_registry_metrics(registry, rf_file, tmp_path, monkeypatch):
    path, x, y = rf_file
    _register("Random Forest", "random_forest", path, inference=False)
    monkeypatch.setattr(preprocess, "features_212_for_file", lambda p: x[y == 4][0])
    result = baseline_service.run_random_forest("bat-ky.wav")
    assert result["name"] == "Random Forest" and result["probs"].shape == (8,) and int(np.argmax(result["probs"])) == 4
    assert result["accuracy"] == 51.11 and result["macro_f1"] == 46.39 and result["latency_ms"] >= 0


def test_run_random_forest_reports_each_failure_in_vietnamese(registry, tmp_path, monkeypatch):
    with pytest.raises(baseline_service.BaselineNotReady, match="Chưa đăng ký"):
        baseline_service.run_random_forest("a.wav")
    _register("Random Forest", "random_forest", str(tmp_path / "da-xoa.pkl"), inference=False)
    with pytest.raises(baseline_service.BaselineNotReady, match="Không thấy tệp"):
        baseline_service.run_random_forest("a.wav")
    broken = tmp_path / "hong.pkl"
    broken.write_bytes(b"day khong phai pickle")
    _register("Random Forest", "random_forest", str(broken), inference=False)
    with pytest.raises(baseline_service.BaselineNotReady, match="Không chạy được"):
        baseline_service.run_random_forest(_wav(tmp_path / "a.wav"))

    def down():
        raise model_service.RegistryUnavailable("db down")

    monkeypatch.setattr(model_service, "baseline_model", lambda family="random_forest": down())
    with pytest.raises(baseline_service.BaselineNotReady, match="Chưa đọc được"):
        baseline_service.run_random_forest("a.wav")


# ---------- giao diện ----------
MAIN = np.array([0.02, 0.02, 0.03, 0.03, 0.80, 0.04, 0.03, 0.03])
RF_RESULT = {"name": "Random Forest", "probs": np.array([0.1, 0.1, 0.1, 0.1, 0.3, 0.1, 0.1, 0.1]), "latency_ms": 44.2, "accuracy": 51.11, "macro_f1": 46.39}


def test_compare_html_shows_both_models_verdict_and_baseline_accuracy():
    html = render.baseline_compare_html("DistilHuBERT + LoRA", MAIN, RF_RESULT)
    assert "DistilHuBERT + LoRA" in html and "Random Forest" in html and "Mô hình chính" in html and "Baseline" in html
    assert "cùng dự đoán «Tức giận»" in html  # cả hai đều chọn nhãn angry
    assert "51,11%" in html and "46,39%" in html and "44,2 ms" in html and "không có biểu đồ XAI" in html
    assert html.count("ev-cmp-row") >= 10  # dòng tiêu đề + dòng dự đoán + 8 cảm xúc


def test_compare_html_reports_disagreement():
    rf = dict(RF_RESULT, probs=np.array([0.5, 0.1, 0.1, 0.1, 0.05, 0.05, 0.05, 0.05]))
    html = render.baseline_compare_html("M", MAIN, rf)
    assert "dự đoán khác nhau" in html and "«Tức giận»" in html and "«Trung tính»" in html


def test_unavailable_html_escapes_message():
    assert "<script>" not in render.baseline_unavailable_html("<script>x</script>")


def test_analysis_adds_baseline_section_only_when_asked(monkeypatch, tmp_path):
    wave = (0.3 * np.sin(np.linspace(0, 400, 48000))).astype(np.float32)
    monkeypatch.setattr(analyze.preprocessing_service, "preprocess_with_duration", lambda p: (wave, 2.0))
    monkeypatch.setattr(analyze.inference_service, "run_inference", lambda w: (MAIN, np.random.default_rng(1).random(149)))
    monkeypatch.setattr(analyze.xai_service, "build_waveform_heatmap", lambda *a: None)
    monkeypatch.setattr(analyze.xai_service, "build_mel_attention", lambda *a: None)
    monkeypatch.setattr(analyze.baseline_service, "run_random_forest", lambda p: RF_RESULT)
    demo = SessionUser(user_id=-1, username="demo", email="d@x")
    audio = _wav(tmp_path / "in.wav")
    with_rf = dict(zip(analyze.OUT_KEYS, list(analyze.run_analysis(audio, None, "upload", demo, True))[-1]))
    assert with_rf["baseline_col"]["visible"] is True and "So sánh với baseline Random Forest" in with_rf["baseline"]["value"]
    without = dict(zip(analyze.OUT_KEYS, list(analyze.run_analysis(audio, None, "upload", demo))[-1]))
    assert without["baseline_col"]["visible"] is False and without["baseline"]["value"] == ""  # mặc định không chạy baseline


def test_baseline_failure_never_breaks_the_main_result(monkeypatch, tmp_path):
    wave = (0.3 * np.sin(np.linspace(0, 400, 48000))).astype(np.float32)
    monkeypatch.setattr(analyze.preprocessing_service, "preprocess_with_duration", lambda p: (wave, 2.0))
    monkeypatch.setattr(analyze.inference_service, "run_inference", lambda w: (MAIN, np.random.default_rng(1).random(149)))
    monkeypatch.setattr(analyze.xai_service, "build_waveform_heatmap", lambda *a: None)
    monkeypatch.setattr(analyze.xai_service, "build_mel_attention", lambda *a: None)
    demo = SessionUser(user_id=-1, username="demo", email="d@x")
    audio = _wav(tmp_path / "in.wav")
    for error in (baseline_service.BaselineNotReady("Chưa đăng ký baseline."), RuntimeError("lỗi bất ngờ")):
        def boom(p, error=error):
            raise error

        monkeypatch.setattr(analyze.baseline_service, "run_random_forest", boom)
        final = dict(zip(analyze.OUT_KEYS, list(analyze.run_analysis(audio, None, "upload", demo, True))[-1]))
        assert final["col_result"]["visible"] is True and "Chưa so sánh được" in final["baseline"]["value"]  # kết quả chính vẫn hiện, baseline báo lỗi
