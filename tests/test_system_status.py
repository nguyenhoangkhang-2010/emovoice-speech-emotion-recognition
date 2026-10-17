# UC06 (nhánh feat/status): trạng thái dịch vụ thật — ứng dụng, mô hình, cơ sở dữ liệu, kho tệp. SQLite trong bộ nhớ + thư mục tạm.
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401  (đăng ký bảng vào Base.metadata)
from core.config import Settings
from core.session import PermissionDenied, SessionUser
from db.base import Base
from ml.config import EMOTION_NAMES, EMOTION_NAMES_VI
from models.emotion import Emotion
from models.user import User
from services import admin_service, model_service
from services import system_status_service as svc

ADMIN = SessionUser(user_id=0, username="demo.admin", email="d@x", role="Admin")  # phiên "Vào thử": không cần dòng trong users


@pytest.fixture()
def env(monkeypatch, tmp_path):
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

    for module in (svc, admin_service):
        monkeypatch.setattr(module, "get_session", fake_get_session)
    for name, attr in (("uploads", "upload_dir"), ("heatmaps", "heatmap_dir"), ("mel", "mel_dir"), ("logs", "log_dir")):
        monkeypatch.setattr(Settings, attr, property(lambda self, n=name: tmp_path / n))
    monkeypatch.setattr(model_service, "active_model", lambda: None)  # mặc định chưa có mô hình; từng test đặt lại khi cần
    with fake_get_session() as s:
        s.add_all(Emotion(emotion_id=i, name=n, name_vi=v) for i, (n, v) in enumerate(zip(EMOTION_NAMES, EMOTION_NAMES_VI)))
        s.commit()
    return fake_get_session, tmp_path


def _by_key(status):
    return {s["key"]: s for s in status["services"]}


def _ckpt(tmp_path, name="m.pt"):
    path = tmp_path / name
    path.write_bytes(b"x")
    return str(path)


def test_four_real_services_with_vietnamese_names(env):
    status = svc.get_system_status(ADMIN)
    assert [s["key"] for s in status["services"]] == ["app", "model", "database", "storage"]
    assert all(set(s) == {"key", "name", "description", "state", "metric"} for s in status["services"])
    assert _by_key(status)["app"]["state"] == "ok" and _by_key(status)["app"]["metric"].startswith("Đã chạy")


def test_database_ok_reports_latency_and_dialect(env):
    database = _by_key(svc.get_system_status(ADMIN))["database"]
    assert database["state"] == "ok" and database["metric"].endswith("ms") and "SQLAlchemy" in database["description"]


def test_database_down_is_red_not_a_crash(env, monkeypatch):
    @contextmanager
    def down():
        raise OperationalError("select 1", {}, Exception("connection refused"))
        yield  # pragma: no cover

    monkeypatch.setattr(svc, "get_session", down)
    monkeypatch.setattr(admin_service, "get_session", down)  # kiểm tra quyền admin cũng cần CSDL: trang vẫn phải báo được
    status = svc.get_system_status(SessionUser(user_id=5, username="boss", email="b@x", role="Admin"))
    database = _by_key(status)["database"]
    assert database["state"] == "bad" and "OperationalError" in database["metric"] and "connection refused" not in database["metric"]  # không lộ chi tiết kết nối
    assert status["overall"] == "bad"


def test_database_missing_seed_data_is_a_warning(env):
    db, _ = env
    with db() as s:
        s.query(Emotion).filter(Emotion.emotion_id > 3).delete()
        s.commit()
    database = _by_key(svc.get_system_status(ADMIN))["database"]
    assert database["state"] == "warn" and "4/8" in database["metric"]


def test_storage_ok_creates_folders_and_leaves_no_probe_files(env):
    _, tmp = env
    storage = _by_key(svc.get_system_status(ADMIN))["storage"]
    assert storage["state"] == "ok" and storage["metric"].startswith("Còn trống")
    assert all((tmp / name).is_dir() for name in ("uploads", "heatmaps", "mel", "logs"))
    assert not list(tmp.rglob(".write-test-*"))  # tệp ghi thử đã được xóa


def test_storage_not_writable_is_red(env, monkeypatch):
    _, tmp = env
    blocker = tmp / "uploads"
    blocker.write_text("là một tệp chứ không phải thư mục")  # không tạo được thư mục cùng tên
    storage = _by_key(svc.get_system_status(ADMIN))["storage"]
    assert storage["state"] == "bad" and storage["metric"].startswith("Không ghi được")


def test_storage_low_disk_space_is_a_warning(env, monkeypatch):
    monkeypatch.setattr(svc.shutil, "disk_usage", lambda path: SimpleNamespace(total=100, used=100, free=200 * 1024**2))
    storage = _by_key(svc.get_system_status(ADMIN))["storage"]
    assert storage["state"] == "warn" and "0.2 GB" in storage["metric"]


# ---------- mô hình ----------
def test_model_without_registry_entry_or_checkpoint_is_red(env, monkeypatch, tmp_path):
    monkeypatch.setattr(Settings, "checkpoint_path", property(lambda self: tmp_path / "khong-co.pt"))
    model = _by_key(svc.get_system_status(ADMIN))["model"]
    assert model["state"] == "bad" and "register_model" in model["metric"]


def test_model_falls_back_to_env_checkpoint_with_warning(env, monkeypatch):
    _, tmp = env
    ckpt = _ckpt(tmp, "env.pt")
    monkeypatch.setattr(Settings, "checkpoint_path", property(lambda self: tmp / "env.pt"))
    model = _by_key(svc.get_system_status(ADMIN))["model"]
    assert model["state"] == "warn" and "dự phòng" in model["description"] and ckpt


def test_model_registered_but_not_loaded_is_ready(env, monkeypatch):
    _, tmp = env
    monkeypatch.setattr(model_service, "active_model", lambda: {"name": "DistilHuBERT + LoRA", "checkpoint_path": _ckpt(tmp)})
    monkeypatch.setattr(svc, "_model_loaded", lambda path: False)
    model = _by_key(svc.get_system_status(ADMIN))["model"]
    assert model["state"] == "ok" and "DistilHuBERT + LoRA đang dùng" == model["description"] and "đầu tiên" in model["metric"]


def test_model_loaded_shows_last_latency(env, monkeypatch):
    _, tmp = env
    monkeypatch.setattr(model_service, "active_model", lambda: {"name": "M", "checkpoint_path": _ckpt(tmp)})
    monkeypatch.setattr(svc, "_model_loaded", lambda path: True)
    from services import inference_service

    monkeypatch.setitem(inference_service._state, "last_latency_ms", 85.4)
    assert _by_key(svc.get_system_status(ADMIN))["model"]["metric"] == "Gần nhất 85 ms/mẫu"
    monkeypatch.setitem(inference_service._state, "last_latency_ms", None)
    assert "chưa có lượt suy luận" in _by_key(svc.get_system_status(ADMIN))["model"]["metric"]


def test_model_with_missing_checkpoint_file_is_red(env, monkeypatch):
    _, tmp = env
    monkeypatch.setattr(model_service, "active_model", lambda: {"name": "M", "checkpoint_path": str(tmp / "da-bi-xoa.pt")})
    model = _by_key(svc.get_system_status(ADMIN))["model"]
    assert model["state"] == "bad" and "checkpoint" in model["metric"]


def test_model_registry_unavailable_is_red(env, monkeypatch):
    def broken():
        raise model_service.RegistryUnavailable("db down")

    monkeypatch.setattr(model_service, "active_model", broken)
    assert _by_key(svc.get_system_status(ADMIN))["model"]["state"] == "bad"


def test_model_loaded_check_does_not_import_torch_and_matches_path(monkeypatch):
    monkeypatch.delitem(__import__("sys").modules, "ml.inference", raising=False)
    assert svc._model_loaded("/x.pt") is False  # chưa import ml.inference => chưa nạp, và không import chỉ để hỏi
    fake = SimpleNamespace(loaded_info=lambda: {"loaded": True, "path": "/x.pt", "device": "cpu"})
    monkeypatch.setitem(__import__("sys").modules, "ml.inference", fake)
    assert svc._model_loaded("/x.pt") is True and svc._model_loaded("/khac.pt") is False


# ---------- tổng hợp và quyền ----------
def test_overall_is_the_worst_service_state(env, monkeypatch):
    monkeypatch.setattr(svc, "_check_model", lambda: {"key": "model", "name": "m", "description": "d", "state": "warn", "metric": ""})
    assert svc.get_system_status(ADMIN)["overall"] == "warn"
    monkeypatch.setattr(svc, "_check_storage", lambda: {"key": "storage", "name": "s", "description": "d", "state": "bad", "metric": ""})
    assert svc.get_system_status(ADMIN)["overall"] == "bad"


def test_uptime_text():
    assert svc._uptime_text(10) == "dưới 1 phút" and svc._uptime_text(300) == "5 phút"
    assert svc._uptime_text(3600 * 2 + 60 * 5) == "2 giờ 5 phút" and svc._uptime_text(86400 * 3 + 3600 * 4) == "3 ngày 4 giờ"


def test_only_admin_can_read_status(env):
    db, _ = env
    with db() as s:
        s.add(User(username="anh", email="a@x.vn", password="h"))
        s.commit()
        user_id = s.query(User).one().user_id
    user = SessionUser(user_id=user_id, username="anh", email="a@x.vn", role="User")
    for who in (user, None):
        with pytest.raises(PermissionDenied):
            svc.get_system_status(who)
    # tự khai Admin trong phiên nhưng CSDL nói là User: bị từ chối ngay
    fake_admin = SessionUser(user_id=user_id, username="anh", email="a@x.vn", role="Admin")
    with pytest.raises(PermissionDenied):
        svc.get_system_status(fake_admin)
