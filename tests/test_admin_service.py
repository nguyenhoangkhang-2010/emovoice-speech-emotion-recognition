# UC06 (nhánh feat/admin): thống kê, danh sách / khóa / cấp mật khẩu tạm cho người dùng, nhật ký hệ thống. SQLite trong bộ nhớ.
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401  (đăng ký bảng vào Base.metadata)
from core.security import verify_password
from core.session import PermissionDenied, SessionUser
from db.base import Base
from ml.config import EMOTION_NAMES, EMOTION_NAMES_VI
from models.audio_file import AudioFile
from models.emotion import Emotion
from models.ml_model import MLModel
from models.password_reset import PasswordReset
from models.prediction import Prediction
from models.system_log import SystemLog
from models.user import User
from services import admin_service as svc

NOW = datetime.now(timezone.utc)


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
    with fake_get_session() as s:
        s.add_all(Emotion(emotion_id=i, name=n, name_vi=v) for i, (n, v) in enumerate(zip(EMOTION_NAMES, EMOTION_NAMES_VI)))
        s.add(MLModel(name="m", model_type="T"))
        s.add_all(
            [
                User(username="admin", email="admin@x.vn", password="h", role="Admin", full_name="Quản trị viên"),
                User(username="anh", email="anh@example.com", password="h", full_name="Nguyễn Anh"),
                User(username="binh", email="binh@example.com", password="h"),
                User(username="chi", email="chi@example.com", password="h", is_active=False),
            ]
        )
        s.commit()
    return fake_get_session


def _session(db, username, role=None):
    with db() as s:
        row = s.query(User).filter_by(username=username).one()
        return SessionUser(user_id=row.user_id, username=row.username, email=row.email, role=role or row.role)


def _predict(db, username, emotion, when):
    with db() as s:
        owner = s.query(User).filter_by(username=username).one()
        audio = AudioFile(user_id=owner.user_id, filename="a.wav", file_path="/up/a.wav", duration=3.0)
        s.add(audio)
        s.flush()
        s.add(Prediction(audio_id=audio.audio_id, model_id=1, emotion_id=EMOTION_NAMES.index(emotion), confidence=0.8, created_at=when))
        s.commit()


def _log(db, level, message, days_ago=0, username=None, service="auth"):
    with db() as s:
        uid = s.query(User).filter_by(username=username).one().user_id if username else None
        s.add(SystemLog(level=level, service=service, message=message, user_id=uid, created_at=NOW - timedelta(days=days_ago)))
        s.commit()


def test_every_admin_function_rejects_non_admin(db):
    user, anonymous = _session(db, "anh"), None
    calls = [
        lambda s: svc.get_stats(s),
        lambda s: svc.list_users(s),
        lambda s: svc.set_user_status(s, 1, False),
        lambda s: svc.reset_user_password(s, 1),
        lambda s: svc.list_logs(s),
        lambda s: svc.list_all_audio(s),
        lambda s: svc.delete_audio(s, 1),
    ]
    for call in calls:
        for who in (user, anonymous):
            with pytest.raises(PermissionDenied):
                call(who)


# ---------- thống kê ----------
def test_stats_count_everything_from_the_database(db):
    admin = _session(db, "admin")
    _predict(db, "anh", "angry", NOW)
    _predict(db, "anh", "angry", NOW - timedelta(days=1))
    _predict(db, "binh", "happy", NOW - timedelta(days=2))
    _predict(db, "binh", "sad", NOW - timedelta(days=10))  # tuần trước
    _predict(db, "binh", "sad", NOW - timedelta(days=40))  # ngoài 7 ngày gần nhất
    stats = svc.get_stats(admin)
    assert stats["analyses"] == 5 and stats["analyses_week"] == 3 and stats["analyses_prev_week"] == 1
    assert stats["accounts"] == 3 and stats["accounts_total"] == 4 and stats["accounts_locked"] == 1
    assert list(stats["distribution"]) == EMOTION_NAMES and stats["distribution"]["angry"] == 2 and stats["distribution"]["happy"] == 1 and stats["distribution"]["sad"] == 2
    assert stats["distribution"]["calm"] == 0  # nhãn chưa có lượt nào vẫn có mặt, bằng 0


def test_stats_daily_series_covers_last_seven_days_oldest_first(db):
    admin = _session(db, "admin")
    _predict(db, "anh", "angry", NOW)
    _predict(db, "anh", "angry", NOW)
    _predict(db, "anh", "happy", NOW - timedelta(days=3))
    _predict(db, "anh", "happy", NOW - timedelta(days=30))
    stats = svc.get_stats(admin)
    assert len(stats["daily_labels"]) == 7 and len(stats["daily_values"]) == 7
    assert stats["daily_values"][-1] == 2 and stats["daily_values"][-4] == 1 and sum(stats["daily_values"]) == 3
    assert set(stats["daily_labels"]) <= {"T2", "T3", "T4", "T5", "T6", "T7", "CN"}


def test_stats_on_empty_database(db):
    with db() as s:
        s.query(User).delete()
        s.commit()
    stats = svc.get_stats(SessionUser(user_id=0, username="demo.admin", email="d@x", role="Admin"))
    assert stats["analyses"] == 0 and stats["accounts"] == 0 and stats["daily_values"] == [0] * 7 and set(stats["distribution"].values()) == {0}


# ---------- người dùng ----------
def test_list_users_has_usage_and_status(db):
    _predict(db, "anh", "angry", NOW)
    _predict(db, "anh", "angry", NOW)
    rows, total = svc.list_users(_session(db, "admin"))
    assert total == 4 and [r["username"] for r in rows] == ["admin", "anh", "binh", "chi"]
    by_name = {r["username"]: r for r in rows}
    assert by_name["anh"]["usage"] == 2 and by_name["binh"]["usage"] == 0
    assert by_name["chi"]["active"] is False and by_name["anh"]["active"] is True and by_name["admin"]["role"] == "Admin"
    assert by_name["anh"]["full_name"] == "Nguyễn Anh" and "password" not in by_name["anh"]  # không bao giờ trả băm mật khẩu


def test_list_users_search_and_pagination(db):
    admin = _session(db, "admin")
    assert [r["username"] for r in svc.list_users(admin, q="EXAMPLE")[0]] == ["anh", "binh", "chi"]  # tìm trong email, không phân biệt hoa/thường
    assert [r["username"] for r in svc.list_users(admin, q="nguyễn")[0]] == ["anh"]  # tìm trong họ tên
    assert svc.list_users(admin, q="%")[1] == 0  # '%' là ký tự thường
    page1, total = svc.list_users(admin, page=1, page_size=3)
    page2, _ = svc.list_users(admin, page=2, page_size=3)
    assert total == 4 and len(page1) == 3 and [r["username"] for r in page2] == ["chi"]
    assert len(svc.list_users(admin, page=1, page_size=10_000)[0]) == 4 and svc.list_users(admin, page=0)[0] == svc.list_users(admin, page=1)[0]


def test_lock_and_unlock_write_logs(db):
    admin = _session(db, "admin")
    anh = _session(db, "anh")
    svc.set_user_status(admin, anh.user_id, False)
    with db() as s:
        assert s.get(User, anh.user_id).is_active is False
        assert any("khóa tài khoản anh" in r.message and r.user_id == admin.user_id for r in s.query(SystemLog))
    svc.set_user_status(admin, anh.user_id, True)
    with db() as s:
        assert s.get(User, anh.user_id).is_active is True
        assert any("mở khóa tài khoản anh" in r.message for r in s.query(SystemLog))


def test_admin_cannot_lock_self_but_unknown_user_is_rejected(db):
    admin = _session(db, "admin")
    with pytest.raises(ValueError, match="tự khóa"):
        svc.set_user_status(admin, admin.user_id, False)
    with pytest.raises(ValueError, match="Không tìm thấy"):
        svc.set_user_status(admin, 9999, False)
    svc.set_user_status(admin, admin.user_id, True)  # mở khóa chính mình thì vô hại
    with db() as s:
        assert s.get(User, admin.user_id).is_active is True


def test_locked_user_cannot_log_in_afterwards(db, monkeypatch):
    from core.security import hash_password
    from services import auth_service

    monkeypatch.setattr(auth_service, "get_session", svc.get_session)
    auth_service._failures.clear()
    with db() as s:
        s.query(User).filter_by(username="anh").one().password = hash_password("matkhau-123")
        s.commit()
    assert auth_service.login("anh", "matkhau-123").username == "anh"
    svc.set_user_status(_session(db, "admin"), _session(db, "anh").user_id, False)
    with pytest.raises(ValueError, match="bị khóa"):
        auth_service.login("anh", "matkhau-123")


def test_reset_user_password_gives_one_time_temp_password(db):
    admin = _session(db, "admin")
    anh = _session(db, "anh")
    with db() as s:
        s.add(PasswordReset(user_id=anh.user_id, token_hash="x" * 64, expires_at=NOW + timedelta(minutes=10)))
        s.commit()
    temp = svc.reset_user_password(admin, anh.user_id)
    assert len(temp) >= 8 and temp != svc.reset_user_password(admin, anh.user_id)  # mỗi lần một mật khẩu khác nhau
    with db() as s:
        row = s.get(User, anh.user_id)
        assert row.password != temp and row.password.startswith("$2")  # chỉ lưu băm bcrypt
        assert s.query(PasswordReset).one().used_at is not None  # mã đặt lại đang chờ mất tác dụng
        logs = [r.message for r in s.query(SystemLog)]
        assert any("cấp mật khẩu tạm cho tài khoản anh" in m for m in logs) and not any(temp in m for m in logs)  # nhật ký không chứa mật khẩu
    with db() as s:
        assert verify_password(svc.reset_user_password(admin, anh.user_id), s.get(User, anh.user_id).password)


def test_reset_user_password_rejects_unknown_user(db):
    with pytest.raises(ValueError, match="Không tìm thấy"):
        svc.reset_user_password(_session(db, "admin"), 9999)


# ---------- nhật ký ----------
def test_list_logs_newest_first_with_user_names(db):
    _log(db, "INFO", "Đăng nhập: anh", days_ago=2, username="anh")
    _log(db, "ERROR", "Lỗi nạp mô hình", days_ago=0, service="model")
    _log(db, "WARNING", "Đăng nhập thất bại", days_ago=1, username="binh")
    rows, total = svc.list_logs(_session(db, "admin"))
    assert total == 3 and [r["message"] for r in rows] == ["Lỗi nạp mô hình", "Đăng nhập thất bại", "Đăng nhập: anh"]
    assert rows[0]["user"] is None and rows[1]["user"] == "binh" and rows[0]["service"] == "model" and rows[0]["level"] == "ERROR"


def test_list_logs_filters(db):
    admin = _session(db, "admin")
    _log(db, "INFO", "Đăng nhập: anh", days_ago=2, username="anh")
    _log(db, "ERROR", "Lỗi nạp mô hình", days_ago=0, service="model")
    _log(db, "WARNING", "Đăng nhập thất bại", days_ago=1, username="binh")
    assert [r["level"] for r in svc.list_logs(admin, level="ERROR")[0]] == ["ERROR"]
    assert [r["message"] for r in svc.list_logs(admin, q="nhập")[0]] == ["Đăng nhập thất bại", "Đăng nhập: anh"]
    assert [r["message"] for r in svc.list_logs(admin, q="MODEL")[0]] == ["Lỗi nạp mô hình"]  # tìm cả trong tên dịch vụ
    assert svc.list_logs(admin, q="khong-co") == ([], 0)
    day = (datetime.now().astimezone() - timedelta(days=2)).date().isoformat()
    assert [r["message"] for r in svc.list_logs(admin, on_date=day)[0]] == ["Đăng nhập: anh"]
    assert svc.list_logs(admin, level="INFO", q="nhập", on_date=day)[1] == 1  # kết hợp nhiều bộ lọc
    assert svc.list_logs(admin, on_date="")[1] == 3 and svc.list_logs(admin, on_date="  ")[1] == 3  # ô ngày để trống = không lọc


def test_list_logs_rejects_bad_input_and_paginates(db):
    admin = _session(db, "admin")
    with pytest.raises(ValueError, match="Ngày không hợp lệ"):
        svc.list_logs(admin, on_date="17/10/2026")
    with pytest.raises(ValueError, match="Mức nhật ký"):
        svc.list_logs(admin, level="DEBUG")
    for i in range(25):
        _log(db, "INFO", f"dòng {i:02d}", days_ago=0)
    page1, total = svc.list_logs(admin, page=1, page_size=10)
    page3, _ = svc.list_logs(admin, page=3, page_size=10)
    assert total == 25 and len(page1) == 10 and len(page3) == 5
    assert len({r["id"] for r in page1} | {r["id"] for r in svc.list_logs(admin, page=2, page_size=10)[0]} | {r["id"] for r in page3}) == 25
