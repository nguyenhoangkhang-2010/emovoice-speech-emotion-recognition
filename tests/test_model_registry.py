# Danh mục mô hình thật (model_service + ml.evaluate + ml.benchmark). SQLite trong bộ nhớ, không nạp mô hình PyTorch nặng.
from contextlib import contextmanager

import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401  (đăng ký bảng vào Base.metadata)
from core.session import PermissionDenied, SessionUser
from db.base import Base
from ml import benchmark, evaluate
from ml.config import CREMAD6_NAMES, CREMAD6_NAMES_VI
from models.system_log import SystemLog
from services import model_service as svc
from ui import render
from ui.pages import model_performance

ADMIN = SessionUser(user_id=0, username="demo.admin", email="a@x.vn", role="Admin")
USER = SessionUser(user_id=-1, username="demo.user", email="u@x.vn")


@pytest.fixture()
def db(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False)

    @contextmanager
    def fake_get_session():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    monkeypatch.setattr(svc, "get_session", fake_get_session)
    return fake_get_session


def _register(name, accuracy=70.0, activate=False, **extra):
    confusion = {"labels": ["a"], "labels_vi": ["A"], "support": [1], "matrix_counts": [[1]], "matrix_normalized": [[1.0]]}
    args = dict(
        name=name, model_type="Transformer", checkpoint_path=f"/tmp/{name}.pt", accuracy=accuracy, f1_score=accuracy - 2, size_mb=90.6,
        inference_time=12.5, params_total=1000, params_trainable=10, eval_dataset="tập thử", eval_samples=180, latency_device="cpu",
        details={"confusion": confusion, "latency": {"batch_size": 1}}, activate=activate,
    )
    args.update(extra)
    return svc.register_model(**args)


def test_empty_registry(db):
    metrics = svc.load_metrics()
    assert metrics["models"] == [] and metrics["active_model"] is None and svc.active_model() is None
    assert svc.confusion_matrix_options() == [] and svc.load_confusion_matrix("1") is None


def test_register_reads_back_real_fields(db):
    saved = _register("A", activate=True)
    assert saved["status"] == "active" and saved["trainable_ratio_pct"] == 1.0
    active = svc.active_model()
    assert active["name"] == "A" and active["accuracy"] == 70.0 and active["size_mib"] == 90.6 and active["latency_device"] == "cpu"
    assert "cpu" in active["latency_note"] and svc.load_metrics()["test_samples"] == 180


def test_register_same_name_updates_instead_of_duplicating(db):
    _register("A", accuracy=60.0)
    _register("A", accuracy=75.5)
    models_ = svc.load_metrics()["models"]
    assert len(models_) == 1 and models_[0]["accuracy"] == 75.5


def test_only_one_model_is_active(db):
    _register("A", activate=True)
    _register("B", accuracy=80.0, activate=True)
    by_name = {m["name"]: m["status"] for m in svc.load_metrics()["models"]}
    assert by_name == {"A": "ready", "B": "active"}
    assert [m["name"] for m in svc.load_metrics()["models"]] == ["B", "A"]


def test_set_active_model_requires_admin_and_logs(db):
    _register("A", activate=True)
    b = _register("B")
    with pytest.raises(PermissionDenied):
        svc.set_active_model(USER, b["key"])
    with pytest.raises(PermissionDenied):
        svc.set_active_model(None, b["key"])
    assert svc.set_active_model(ADMIN, b["key"])["name"] == "B"
    assert svc.active_model()["name"] == "B"
    with db() as s:
        assert any("Đặt mô hình đang dùng: B" in log.message for log in s.query(SystemLog))
    with pytest.raises(ValueError):
        svc.set_active_model(ADMIN, "999")
    with pytest.raises(ValueError):
        svc.set_active_model(ADMIN, "khong-phai-so")


def test_baseline_is_comparison_only(db):
    _register("A", activate=True)
    rf = _register("RF", accuracy=50.0, details={"inference": False, "confusion": {"labels": []}})
    assert rf["can_infer"] is False and svc.active_model()["name"] == "A"
    with pytest.raises(ValueError, match="baseline"):
        svc.set_active_model(ADMIN, rf["key"])
    with pytest.raises(ValueError, match="baseline"):
        _register("RF", activate=True, details={"inference": False})
    assert svc.active_model()["name"] == "A"  # lần kích hoạt lỗi không làm mất mô hình đang dùng


def test_confusion_matrix_lookup(db):
    a = _register("A")
    assert svc.load_confusion_matrix(a["key"])["matrix_normalized"] == [[1.0]]
    assert svc.confusion_matrix_options() == [("A", a["key"])]
    assert svc.load_confusion_matrix("12345") is None


def test_unavailable_database_is_reported_clearly(monkeypatch):
    @contextmanager
    def broken():
        from sqlalchemy.exc import OperationalError

        raise OperationalError("select", {}, Exception("no such table"))
        yield  # pragma: no cover

    monkeypatch.setattr(svc, "get_session", broken)
    with pytest.raises(svc.RegistryUnavailable):
        svc.load_metrics()


def test_compute_metrics_and_confusion():
    y_true = [0, 0, 1, 1, 2, 2, 3, 3]
    y_pred = [0, 0, 1, 2, 2, 2, 3, 0]
    result = evaluate.compute_metrics(y_true, y_pred)
    assert result["accuracy"] == 75.0
    assert result["per_class"][0]["recall"] == 100.0 and result["per_class"][1]["recall"] == 50.0
    assert result["per_class"][4]["support"] == 0  # lớp không có mẫu: không chia cho 0
    norm = evaluate.confusion_matrix_normalized(y_true, y_pred)
    assert norm.shape == (8, 8) and np.allclose(norm[:4].sum(axis=1), 1.0) and np.allclose(norm[4:], 0.0)
    summary = evaluate.summarize(y_true, y_pred)
    assert summary["confusion"]["matrix_counts"][1][2] == 1 and len(summary["confusion"]["labels_vi"]) == 8


def test_load_eval_set(tmp_path):
    good = tmp_path / "ok.npz"
    np.savez(good, X_test=np.zeros((3, 48000), dtype=np.float32), y_test=np.array([0, 1, 2]))
    x, y = evaluate.load_eval_set(good)
    assert x.shape == (3, 48000) and y.tolist() == [0, 1, 2]
    bad = tmp_path / "bad.npz"
    np.savez(bad, X_test=np.zeros((3, 100), dtype=np.float32), y_test=np.array([0, 1, 2]))
    with pytest.raises(ValueError):
        evaluate.load_eval_set(bad)
    with pytest.raises(FileNotFoundError):
        evaluate.load_eval_set(tmp_path / "khong-co.npz")


def test_benchmark_counts_and_latency(tmp_path):
    torch = pytest.importorskip("torch")
    net = torch.nn.Sequential(torch.nn.Linear(4, 3), torch.nn.Linear(3, 2))
    for p in net[0].parameters():
        p.requires_grad = False
    counts = benchmark.count_parameters(net)
    assert counts == {"total": 4 * 3 + 3 + 3 * 2 + 2, "trainable": 3 * 2 + 2}
    file = tmp_path / "w.bin"
    file.write_bytes(b"x" * (1024 * 1024))
    assert benchmark.checkpoint_size_mib(file) == 1.0
    calls = []
    assert benchmark.measure_latency_ms(lambda s: calls.append(s), "mẫu", warmup=2, repeats=5) >= 0
    assert len(calls) == 7


# ---------- mô hình CREMA-D 6 nhãn: chỉ để so sánh với mô hình chính RAVDESS 8 nhãn ----------
def _register_cremad(name="CREMA-D", accuracy=68.35):
    summary = evaluate.summarize([0, 1, 2, 3, 4, 5, 5], [0, 1, 2, 3, 4, 5, 0], "cremad6")
    details = {"inference": False, "family": "cremad6", "labels": CREMAD6_NAMES, "labels_vi": CREMAD6_NAMES_VI, "dataset_label": "CREMA-D", "confusion": summary["confusion"]}
    return svc.register_model(
        name=name, model_type="Transformer", checkpoint_path=f"/tmp/{name}.pt", accuracy=accuracy, f1_score=67.96, size_mb=0.96,
        inference_time=130.0, params_total=23000000, params_trainable=248839, eval_dataset="CREMA-D 15 diễn viên test (cremad_test.npz)",
        eval_samples=1229, latency_device="cpu", details=details,
    )


def test_evaluate_with_six_label_set():
    y_true, y_pred = [0, 1, 2, 3, 4, 5, 5], [0, 1, 2, 3, 4, 5, 0]
    result = evaluate.compute_metrics(y_true, y_pred, "cremad6")
    assert [c["label"] for c in result["per_class"]] == CREMAD6_NAMES and result["accuracy"] == round(6 / 7 * 100, 2)
    summary = evaluate.summarize(y_true, y_pred, "cremad6")
    assert len(summary["confusion"]["matrix_counts"]) == 6 and summary["confusion"]["labels_vi"] == CREMAD6_NAMES_VI
    assert evaluate.confusion_matrix_normalized(y_true, y_pred, "cremad6").shape == (6, 6)
    assert evaluate.confusion_matrix_normalized(y_true, y_pred).shape == (8, 8)  # mặc định vẫn là 8 nhãn


def test_load_eval_set_accepts_cremad_array_names(tmp_path):
    cremad = tmp_path / "cremad_test.npz"
    np.savez(cremad, X=np.zeros((2, 48000), dtype=np.float32), y=np.array([0, 5]), n=np.array([48000, 40000]))
    x, y = evaluate.load_eval_set(cremad)
    assert x.shape == (2, 48000) and y.tolist() == [0, 5]
    wrong = tmp_path / "sai.npz"
    np.savez(wrong, A=np.zeros((2, 48000), dtype=np.float32))
    with pytest.raises(ValueError, match="X_test"):
        evaluate.load_eval_set(wrong)


def test_cremad_model_is_registered_for_comparison_only(db):
    main = _register("A", accuracy=75.0, activate=True)
    cremad = _register_cremad()
    assert cremad["classes"] == 6 and cremad["dataset_label"] == "CREMA-D" and cremad["can_infer"] is False and main["classes"] == 8
    assert svc.active_model()["name"] == "A"
    with pytest.raises(ValueError, match="so sánh"):
        svc.set_active_model(ADMIN, cremad["key"])
    with pytest.raises(ValueError, match="so sánh"):
        svc.register_model(
            name="CREMA-D khác", model_type="T", checkpoint_path="x", accuracy=1, f1_score=1, size_mb=1, inference_time=1, params_total=1, params_trainable=1,
            eval_dataset="x", eval_samples=1, latency_device="cpu", details={"inference": False}, activate=True,
        )
    assert svc.baseline_model("cremad6")["name"] == "CREMA-D"
    matrix = svc.load_confusion_matrix(cremad["key"])
    assert len(matrix["matrix_normalized"]) == 6 and matrix["labels_vi"] == CREMAD6_NAMES_VI


def test_models_page_compares_only_within_same_label_set(db):
    _register("A", accuracy=75.0, activate=True)
    _register("RF", accuracy=51.0)
    _register_cremad(accuracy=68.35)
    metrics = svc.load_metrics()
    delta, _, _ = model_performance._footers(metrics)
    assert "RF" in delta and "CREMA-D" not in delta  # chênh lệch chỉ so với mô hình cùng bộ nhãn
    sub = model_performance._table_sub(metrics)
    assert "không so sánh trực tiếp" in sub and "12,5% với 8 nhãn" in sub and "16,7% với 6 nhãn" in sub


def test_models_page_without_other_label_set_keeps_the_single_dataset_text(db):
    _register("A", accuracy=75.0, activate=True)
    assert "không so sánh trực tiếp" not in model_performance._table_sub(svc.load_metrics())


def test_models_table_shows_dataset_and_label_count(db):
    _register("A", accuracy=75.0, activate=True)
    _register_cremad()
    html = render.models_table_html(svc.load_metrics()["models"], svc.load_metrics()["active_model"])
    assert "Tập kiểm thử" in html and "CREMA-D · 6 nhãn" in html and "tập thử · 8 nhãn" in html


def test_confusion_matrix_grid_follows_label_count(db):
    cremad = _register_cremad()
    html = render.confusion_matrix_html(svc.load_confusion_matrix(cremad["key"]))
    assert html.count("grid-template-columns:repeat(7, 1fr)") == 7  # 1 hàng tiêu đề + 6 hàng nhãn, mỗi hàng 6 nhãn + cột tên
    assert "Trung tính" in html and "Ngạc nhiên" not in html


def test_real_cremad_checkpoint_loads_into_the_six_class_model():
    torch = pytest.importorskip("torch")
    from core.config import PROJECT_DIR
    from ml.inference import build_model

    ckpt = PROJECT_DIR / "ml" / "weights" / "cremad6_distilhubert_lora.pt"
    if not ckpt.exists():
        pytest.skip("Chưa có ml/weights/cremad6_distilhubert_lora.pt")
    model = build_model(ckpt, torch.device("cpu"), num_classes=6)
    with torch.no_grad():
        logits, attn = model(torch.zeros(1, 48000))
    assert tuple(logits.shape) == (1, 6) and attn.shape[1] == 149
