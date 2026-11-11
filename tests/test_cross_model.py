# So sánh trực tiếp trên trang Phân tích: chạy thêm mô hình CREMA-D 6 nhãn trên cùng đoạn âm thanh (services.cross_model_service + ui.render).
from contextlib import contextmanager

import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401  (đăng ký bảng vào Base.metadata)
from core.session import SessionUser
from db.base import Base
from ml.config import CREMAD6_NAMES
from services import cross_model_service as svc
from services import model_service
from ui import render
from ui.pages import analyze

MAIN = np.array([0.02, 0.02, 0.03, 0.03, 0.80, 0.04, 0.03, 0.03])  # tức giận
OTHER = {"name": "CREMA-D", "probs": np.array([0.05, 0.05, 0.05, 0.70, 0.10, 0.05]), "labels": CREMAD6_NAMES, "latency_ms": 88.4, "accuracy": 68.35, "macro_f1": 67.96}
WAVE = (0.3 * np.sin(np.linspace(0, 400, 48000))).astype(np.float32)


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


def _register_cremad(checkpoint):
    return model_service.register_model(
        name="CREMA-D", model_type="Transformer", checkpoint_path=str(checkpoint), accuracy=68.35, f1_score=67.96, size_mb=1.0, inference_time=1.0,
        params_total=None, params_trainable=None, eval_dataset="CREMA-D", eval_samples=1229, latency_device="cpu",
        details={"inference": False, "family": "cremad6", "labels": CREMAD6_NAMES, "confusion": {"labels": []}},
    )


# ---------- dịch vụ ----------
def test_run_cremad6_returns_six_probs_and_registry_metrics(registry, tmp_path, monkeypatch):
    ckpt = tmp_path / "c.pt"
    ckpt.write_bytes(b"x")
    _register_cremad(ckpt)
    seen = {}

    def fake_predict(wave, path, num_classes):
        seen.update(path=path, n=num_classes, size=len(wave))
        return np.array([0.1, 0.1, 0.1, 0.5, 0.1, 0.1])

    from ml import inference

    monkeypatch.setattr(inference, "predict_aux", fake_predict)
    result = svc.run_cremad6(WAVE)
    assert result["name"] == "CREMA-D" and result["labels"] == CREMAD6_NAMES and int(np.argmax(result["probs"])) == 3
    assert result["accuracy"] == 68.35 and result["macro_f1"] == 67.96 and result["latency_ms"] >= 0
    assert seen == {"path": str(ckpt), "n": 6, "size": 48000}


def test_run_cremad6_reports_each_failure_in_vietnamese(registry, tmp_path, monkeypatch):
    with pytest.raises(svc.CrossModelNotReady, match="Chưa đăng ký"):
        svc.run_cremad6(WAVE)
    _register_cremad(tmp_path / "da-xoa.pt")
    with pytest.raises(svc.CrossModelNotReady, match="Không thấy tệp"):
        svc.run_cremad6(WAVE)
    broken = tmp_path / "hong.pt"
    broken.write_bytes(b"khong phai checkpoint")
    _register_cremad(broken)
    with pytest.raises(svc.CrossModelNotReady, match="Không chạy được"):
        svc.run_cremad6(WAVE)

    def down(family):
        raise model_service.RegistryUnavailable("db down")

    monkeypatch.setattr(model_service, "comparison_model", down)
    with pytest.raises(svc.CrossModelNotReady, match="Chưa đọc được"):
        svc.run_cremad6(WAVE)


def test_cremad_model_is_not_picked_up_as_the_random_forest_baseline(registry, tmp_path):
    ckpt = tmp_path / "c.pt"
    ckpt.write_bytes(b"x")
    _register_cremad(ckpt)
    assert model_service.baseline_model("random_forest") is None and model_service.comparison_model("cremad6")["name"] == "CREMA-D"


def test_real_cremad_checkpoint_gives_six_probabilities_and_is_cached():
    pytest.importorskip("torch")
    from core.config import PROJECT_DIR
    from ml import inference

    ckpt = PROJECT_DIR / "ml" / "weights" / "cremad6_distilhubert_lora.pt"
    if not ckpt.exists():
        pytest.skip("Chưa có ml/weights/cremad6_distilhubert_lora.pt")
    probs = inference.predict_aux(WAVE, str(ckpt), 6)
    assert probs.shape == (6,) and abs(float(probs.sum()) - 1.0) < 1e-4
    assert str(ckpt) in inference._aux_models
    first = inference._aux_models[str(ckpt)][0]
    inference.predict_aux(WAVE, str(ckpt), 6)
    assert inference._aux_models[str(ckpt)][0] is first  # nạp một lần, lần sau dùng lại
    with pytest.raises(ValueError, match="48000"):
        inference.predict_aux(WAVE[:100], str(ckpt), 6)


# ---------- giao diện ----------
def test_cross_compare_shows_all_eight_system_labels_and_blanks_the_two_missing_ones():
    html = render.cross_compare_html("DistilHuBERT + LoRA", MAIN, OTHER)
    assert "So sánh với mô hình CREMA-D 6 nhãn" in html and "DistilHuBERT + LoRA" in html and "CREMA-D · 6 nhãn" in html
    assert html.count("Không có nhãn") == 2  # «Êm đềm» và «Ngạc nhiên» không có trong CREMA-D
    assert html.count("ev-cmp-row") >= 10 and "68,35%" in html and "67,96%" in html and "88,4 ms" in html and "không so trực tiếp" in html


def test_cross_compare_verdicts():
    agree = render.cross_compare_html("M", MAIN, dict(OTHER, probs=np.array([0.05, 0.05, 0.05, 0.70, 0.10, 0.05]), labels=CREMAD6_NAMES))
    assert "cùng dự đoán «Tức giận»" in agree
    differ = render.cross_compare_html("M", MAIN, dict(OTHER, probs=np.array([0.6, 0.1, 0.1, 0.05, 0.1, 0.05])))
    assert "dự đoán khác nhau" in differ and "«Tức giận»" in differ and "«Trung tính»" in differ
    calm = np.array([0.02, 0.80, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03])  # nhãn chính là «Êm đềm»: CREMA-D không có nhãn này
    missing = render.cross_compare_html("M", calm, OTHER)
    assert "Êm đềm" in missing and "không có trong bộ 6 nhãn" in missing


def test_unavailable_html_uses_the_given_title_and_escapes_message():
    html = render.baseline_unavailable_html("<b>x</b>", "Chưa so sánh được với mô hình CREMA-D")
    assert "mô hình CREMA-D" in html and "<b>x</b>" not in html
    assert "baseline" in render.baseline_unavailable_html("x")  # mặc định vẫn là tiêu đề của baseline


# ---------- trang Phân tích ----------
def _patch_main(monkeypatch):
    monkeypatch.setattr(analyze.preprocessing_service, "preprocess_with_duration", lambda p: (WAVE, 2.0))
    monkeypatch.setattr(analyze.inference_service, "run_inference", lambda w: (MAIN, np.random.default_rng(1).random(149)))
    monkeypatch.setattr(analyze.xai_service, "build_waveform_heatmap", lambda *a: None)
    monkeypatch.setattr(analyze.xai_service, "build_mel_attention", lambda *a: None)


def _wav(path):
    import soundfile as sf

    sf.write(str(path), WAVE[:16000], 16000)
    return str(path)


def test_analysis_adds_cremad_section_only_when_asked(monkeypatch, tmp_path):
    _patch_main(monkeypatch)
    monkeypatch.setattr(analyze.cross_model_service, "run_cremad6", lambda w: OTHER)
    demo = SessionUser(user_id=-1, username="demo", email="d@x")
    audio = _wav(tmp_path / "in.wav")
    with_it = dict(zip(analyze.OUT_KEYS, list(analyze.run_analysis(audio, None, "upload", demo, ["cremad6"]))[-1]))
    assert with_it["cremad_col"]["visible"] is True and "So sánh với mô hình CREMA-D 6 nhãn" in with_it["cremad"]["value"]
    assert with_it["baseline_col"]["visible"] is False  # hai ô so sánh độc lập nhau
    without = dict(zip(analyze.OUT_KEYS, list(analyze.run_analysis(audio, None, "upload", demo))[-1]))
    assert without["cremad_col"]["visible"] is False and without["cremad"]["value"] == ""


def test_dropdown_selection_decides_which_comparisons_run(monkeypatch, tmp_path):
    _patch_main(monkeypatch)
    monkeypatch.setattr(analyze.cross_model_service, "run_cremad6", lambda w: OTHER)
    rf = {"name": "Random Forest", "probs": np.full(8, 0.125), "latency_ms": 40.0, "accuracy": 51.11, "macro_f1": 46.39}
    monkeypatch.setattr(analyze.baseline_service, "run_random_forest", lambda p: rf)
    demo = SessionUser(user_id=-1, username="demo", email="d@x")
    audio = _wav(tmp_path / "in.wav")

    def run(choice):
        return dict(zip(analyze.OUT_KEYS, list(analyze.run_analysis(audio, None, "upload", demo, choice))[-1]))

    for choice, rf_shown, cremad_shown in ((None, False, False), ([], False, False), (["random_forest"], True, False), (["cremad6"], False, True), (["random_forest", "cremad6"], True, True), (["khong-co"], False, False)):
        final = run(choice)
        assert (final["baseline_col"]["visible"], final["cremad_col"]["visible"]) == (rf_shown, cremad_shown), choice
        assert final["col_result"]["visible"] is True  # kết quả chính luôn hiện, dù chọn mô hình nào


def test_compare_dropdown_offers_exactly_the_two_models():
    import gradio as gr

    with gr.Blocks() as demo:
        analyze.build(gr.State(None))
    dropdowns = [b for b in demo.blocks.values() if isinstance(b, gr.Dropdown) and "ev-compare" in (b.elem_classes or [])]
    assert len(dropdowns) == 1 and dropdowns[0].multiselect is True and dropdowns[0].value == []
    assert [value for _, value in dropdowns[0].choices] == [analyze.COMPARE_RF, analyze.COMPARE_CREMAD]


def test_cremad_failure_never_breaks_the_main_result(monkeypatch, tmp_path):
    _patch_main(monkeypatch)
    demo = SessionUser(user_id=-1, username="demo", email="d@x")
    audio = _wav(tmp_path / "in.wav")
    for error in (svc.CrossModelNotReady("Chưa đăng ký mô hình CREMA-D."), RuntimeError("lỗi bất ngờ")):
        def boom(w, error=error):
            raise error

        monkeypatch.setattr(analyze.cross_model_service, "run_cremad6", boom)
        final = dict(zip(analyze.OUT_KEYS, list(analyze.run_analysis(audio, None, "upload", demo, ["cremad6"]))[-1]))
        assert final["col_result"]["visible"] is True and "Chưa so sánh được với mô hình CREMA-D" in final["cremad"]["value"]


def test_analyze_another_hides_the_cremad_section():
    out = analyze.reset_view()
    state = dict(zip(analyze.OUT_KEYS, out[: len(analyze.OUT_KEYS)]))
    assert state["cremad_col"]["visible"] is False and state["cremad"]["value"] == ""
