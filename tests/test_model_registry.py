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
from models.system_log import SystemLog
from services import model_service as svc

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
    assert [m["name"] for m in svc.load_metrics()["models"]] == ["B", "A"]  # mô hình đang dùng đứng đầu


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
