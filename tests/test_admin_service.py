# Thống kê, danh sách / khóa / cấp mật khẩu tạm cho người dùng, nhật ký hệ thống. SQLite trong bộ nhớ.
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
                User(username="admin", email="admin@x.vn", password="h", role="Admin", is_system_admin=True, full_name="Quản trị viên"),
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
        lambda s: svc.set_user_role(s, 1, "Admin"),
        lambda s: svc.delete_user(s, 1),
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
    _predict(db, "binh", "sad", NOW - timedelta(days=10))
    _predict(db, "binh", "sad", NOW - timedelta(days=40))
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
    assert by_name["anh"]["full_name"] == "Nguyễn Anh" and "password" not in by_name["anh"]


def test_list_users_search_and_pagination(db):
    admin = _session(db, "admin")
    assert [r["username"] for r in svc.list_users(admin, q="EXAMPLE")[0]] == ["anh", "binh", "chi"]  # tìm trong email, không phân biệt hoa/thường
    assert [r["username"] for r in svc.list_users(admin, q="nguyễn")[0]] == ["anh"]
    assert svc.list_users(admin, q="%")[1] == 0
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
    svc.set_user_status(admin, admin.user_id, True)
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
    assert len(temp) >= 8 and temp != svc.reset_user_password(admin, anh.user_id)
    with db() as s:
        row = s.get(User, anh.user_id)
        assert row.password != temp and row.password.startswith("$2")
        assert s.query(PasswordReset).one().used_at is not None
        logs = [r.message for r in s.query(SystemLog)]
        assert any("cấp mật khẩu tạm cho tài khoản anh" in m for m in logs) and not any(temp in m for m in logs)
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
    assert [r["message"] for r in svc.list_logs(admin, q="MODEL")[0]] == ["Lỗi nạp mô hình"]
    assert svc.list_logs(admin, q="khong-co") == ([], 0)
    day = (datetime.now().astimezone() - timedelta(days=2)).date().isoformat()
    assert [r["message"] for r in svc.list_logs(admin, on_date=day)[0]] == ["Đăng nhập: anh"]
    assert svc.list_logs(admin, level="INFO", q="nhập", on_date=day)[1] == 1
    assert svc.list_logs(admin, on_date="")[1] == 3 and svc.list_logs(admin, on_date="  ")[1] == 3


def test_log_calendar_bounds_future_dates_rejected_and_first_log_date(db):
    admin = _session(db, "admin")
    assert svc.first_log_date(admin) is None  # chưa có dòng nhật ký nào thì lịch không có cận dưới
    _log(db, "INFO", "mới", days_ago=1)
    _log(db, "INFO", "cũ nhất", days_ago=5)
    assert svc.first_log_date(admin) == (datetime.now().astimezone() - timedelta(days=5)).date()
    tomorrow = (datetime.now().astimezone() + timedelta(days=1)).date().isoformat()
    with pytest.raises(ValueError, match="chưa tới"):
        svc.list_logs(admin, on_date=tomorrow)
    today = datetime.now().astimezone().date().isoformat()
    assert svc.list_logs(admin, on_date=today)[1] == 0  # hôm nay chọn được (chưa có dòng nào)
    with pytest.raises(PermissionDenied):
        svc.first_log_date(_session(db, "anh"))


def test_list_logs_filters_by_date_range(db):
    admin = _session(db, "admin")
    for days_ago, message in [(0, "hôm nay"), (1, "hôm qua"), (3, "ba ngày trước"), (10, "mười ngày trước")]:
        _log(db, "INFO", message, days_ago=days_ago)
    day = lambda n: (datetime.now().astimezone() - timedelta(days=n)).date().isoformat()
    msgs = lambda **kw: [r["message"] for r in svc.list_logs(admin, **kw)[0]]
    assert msgs(date_from=day(3), date_to=day(1)) == ["hôm qua", "ba ngày trước"]
    assert msgs(date_from=day(1)) == ["hôm nay", "hôm qua"]
    assert msgs(date_to=day(3)) == ["ba ngày trước", "mười ngày trước"]
    assert msgs(date_from=day(3), date_to=day(3)) == ["ba ngày trước"]
    assert svc.list_logs(admin, date_from="", date_to=" ")[1] == 4
    with pytest.raises(ValueError, match="bắt đầu"):
        svc.list_logs(admin, date_from=day(1), date_to=day(5))
    with pytest.raises(ValueError, match="chưa tới"):
        svc.list_logs(admin, date_to=(datetime.now().astimezone() + timedelta(days=1)).date().isoformat())
    with pytest.raises(ValueError, match="không hợp lệ"):
        svc.list_logs(admin, date_from="hôm qua")


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


# ---------- cấp / thu hồi quyền quản trị ----------
def test_grant_and_revoke_admin_role_with_warning_logs(db):
    admin = _session(db, "admin")
    anh = _session(db, "anh")
    assert svc.set_user_role(admin, anh.user_id, "Admin") is True
    with db() as s:
        assert s.get(User, anh.user_id).role == "Admin"
        assert any(r.level == "WARNING" and "cấp quyền quản trị cho tài khoản anh" in r.message and r.user_id == admin.user_id for r in s.query(SystemLog))
    assert svc.set_user_role(admin, anh.user_id, "User") is True
    with db() as s:
        assert s.get(User, anh.user_id).role == "User"
        assert any("thu hồi quyền quản trị của tài khoản anh" in r.message for r in s.query(SystemLog))


def test_new_admin_can_use_admin_functions_immediately(db):
    anh = _session(db, "anh")
    with pytest.raises(PermissionDenied):
        svc.list_users(SessionUser(user_id=anh.user_id, username="anh", email="anh@example.com", role="Admin"))  # tự khai Admin trong phiên nhưng CSDL nói User
    svc.set_user_role(_session(db, "admin"), anh.user_id, "Admin")
    fresh = SessionUser(user_id=anh.user_id, username="anh", email="anh@example.com", role="Admin")
    assert svc.list_users(fresh)[1] == 4


def test_role_change_is_noop_when_already_that_role(db):
    admin = _session(db, "admin")
    before = None
    with db() as s:
        before = s.query(SystemLog).count()
    assert svc.set_user_role(admin, _session(db, "anh").user_id, "User") is False
    with db() as s:
        assert s.query(SystemLog).count() == before  # không có thay đổi thì không ghi nhật ký


def test_role_change_guards(db):
    admin = _session(db, "admin")
    with pytest.raises(ValueError, match="tự thu hồi"):
        svc.set_user_role(admin, admin.user_id, "User")
    with pytest.raises(ValueError, match="khóa"):
        svc.set_user_role(admin, _session(db, "chi").user_id, "Admin")
    with pytest.raises(ValueError, match="Vai trò không hợp lệ"):
        svc.set_user_role(admin, _session(db, "anh").user_id, "Root")
    with pytest.raises(ValueError, match="Không tìm thấy"):
        svc.set_user_role(admin, 9999, "Admin")


def test_cannot_remove_the_last_active_admin(db):
    # phiên "Vào thử" không có dòng trong users nên không bị chặn "tự thu quyền", nhưng vẫn không được thu quyền admin duy nhất
    demo = SessionUser(user_id=0, username="demo.admin", email="d@x", role="Admin")
    with pytest.raises(ValueError, match="ít nhất một quản trị viên"):
        svc.set_user_role(demo, _session(db, "admin").user_id, "User")
    with db() as s:
        assert s.query(User).filter_by(username="admin").one().role == "Admin"


def test_demoted_or_locked_admin_loses_access_immediately(db):
    boss = _session(db, "admin")
    anh = _session(db, "anh")
    svc.set_user_role(boss, anh.user_id, "Admin")
    anh_admin = SessionUser(user_id=anh.user_id, username="anh", email="anh@example.com", role="Admin")
    assert svc.get_stats(anh_admin)["accounts_total"] == 4
    svc.set_user_role(boss, anh.user_id, "User")  # bị thu quyền khi phiên admin của anh vẫn đang mở
    for call in (svc.get_stats, svc.list_users, svc.list_logs):
        with pytest.raises(PermissionDenied):
            call(anh_admin)
    svc.set_user_role(boss, anh.user_id, "Admin")
    svc.set_user_status(boss, anh.user_id, False)
    with pytest.raises(PermissionDenied):
        svc.list_users(anh_admin)


# ---------- admin tạo tài khoản ----------
def test_create_user_generates_one_time_temp_password_and_stores_only_the_hash(db):
    admin = _session(db, "admin")
    created = svc.create_user(admin, "Moi.Nguoi", "Moi@Example.com", "User", "  Nguyễn   Mới ")
    assert created["username"] == "Moi.Nguoi" and created["email"] == "moi@example.com" and created["role"] == "User" and len(created["temp_password"]) >= 8
    with db() as s:
        row = s.get(User, created["user_id"])
        assert row.full_name == "Nguyễn Mới" and row.is_active is True and row.role == "User"  # khoảng trắng thừa trong họ tên được gộp
        assert row.password != created["temp_password"] and verify_password(created["temp_password"], row.password)
        logs = [r for r in s.query(SystemLog)]
        assert [(r.level, r.message) for r in logs] == [("INFO", "admin tạo tài khoản Moi.Nguoi (vai trò User)")] and logs[0].user_id == admin.user_id
        assert not any(created["temp_password"] in r.message for r in logs)
    assert svc.create_user(admin, "khac", "khac@example.com")["temp_password"] != created["temp_password"]


def test_created_user_can_log_in_with_the_temp_password(db, monkeypatch):
    from services import auth_service

    monkeypatch.setattr(auth_service, "get_session", svc.get_session)
    auth_service._failures.clear()
    created = svc.create_user(_session(db, "admin"), "nguoimoi", "nguoimoi@example.com")
    assert auth_service.login("nguoimoi", created["temp_password"]).role == "User"
    assert auth_service.login("NGUOIMOI@example.com", created["temp_password"]).username == "nguoimoi"


def test_create_admin_user_is_logged_as_warning(db):
    created = svc.create_user(_session(db, "admin"), "quantri2", "qt2@example.com", "Admin")
    assert created["role"] == "Admin"
    with db() as s:
        assert [(r.level, r.message) for r in s.query(SystemLog)] == [("WARNING", "admin tạo tài khoản quantri2 (vai trò Admin)")]
        assert s.get(User, created["user_id"]).role == "Admin"


@pytest.mark.parametrize(
    "username,email,role,full_name,message",
    [
        ("ab", "a@x.vn", "User", "", "Tên đăng nhập"),
        ("co dau cach", "a@x.vn", "User", "", "Tên đăng nhập"),
        ("hopLe", "khong-phai-email", "User", "", "Email"),
        ("hopLe", "a@x.vn", "Root", "", "Vai trò không hợp lệ"),
        ("hopLe", "a@x.vn", "User", "x" * 101, "tối đa 100"),
        ("ANH", "khac@x.vn", "User", "", "đã được sử dụng"),  # trùng tên đăng nhập 'anh', không phân biệt hoa/thường
        ("khac", "ANH@Example.com", "User", "", "đã được sử dụng"),
    ],
)
def test_create_user_rejects_bad_input_without_creating_anything(db, username, email, role, full_name, message):
    with pytest.raises(ValueError, match=message):
        svc.create_user(_session(db, "admin"), username, email, role, full_name)
    with db() as s:
        assert s.query(User).count() == 4 and s.query(SystemLog).count() == 0


def test_demo_admin_can_create_users_but_non_admin_cannot(db):
    demo = SessionUser(user_id=0, username="demo.admin", email="d@x", role="Admin")
    assert svc.create_user(demo, "tu.demo", "tudemo@example.com")["username"] == "tu.demo"
    with db() as s:
        assert s.query(SystemLog).one().user_id is None  # phiên thử không có dòng trong users nên không gắn người dùng
    with pytest.raises(PermissionDenied):
        svc.create_user(_session(db, "anh"), "x1234", "x@example.com")


# ---------- hai bậc quản trị: admin hệ thống và admin được cấp lên ----------
def _promoted(db, username="anh"):
    """Cấp quyền admin cho `username` (bởi admin hệ thống) rồi trả phiên của họ."""
    boss = _session(db, "admin")
    target = _session(db, username)
    svc.set_user_role(boss, target.user_id, "Admin")
    return SessionUser(user_id=target.user_id, username=username, email=target.email, role="Admin")


def test_promoted_admin_manages_roles_of_everyone_except_system_admin(db):
    anh = _promoted(db)
    binh = _session(db, "binh")
    assert svc.set_user_role(anh, binh.user_id, "Admin") is True  # admin được cấp lên cũng cấp quyền cho người khác được
    assert svc.set_user_role(anh, binh.user_id, "User") is True  # và thu hồi được
    assert svc.create_user(anh, "quantri3", "qt3@example.com", "Admin")["role"] == "Admin"
    svc.set_user_role(anh, binh.user_id, "Admin")
    assert svc.set_user_role(anh, binh.user_id, "User") is True  # kể cả admin ngang hàng
    with pytest.raises(ValueError, match="được bảo vệ"):
        svc.set_user_role(anh, _session(db, "admin").user_id, "User")  # admin hệ thống thì không ai thu quyền được
    with pytest.raises(ValueError, match="tự thu hồi"):
        svc.set_user_role(anh, anh.user_id, "User")
    with db() as s:
        assert s.query(User).filter_by(username="admin").one().role == "Admin"


def test_promoted_admin_cannot_lock_or_reset_system_admin_but_can_for_other_admins(db):
    anh = _promoted(db)
    boss = _session(db, "admin")
    binh = _promoted(db, "binh")
    with pytest.raises(ValueError, match="được bảo vệ"):
        svc.set_user_status(anh, boss.user_id, False)
    with pytest.raises(ValueError, match="được bảo vệ"):
        svc.reset_user_password(anh, boss.user_id)
    with db() as s:
        assert s.query(User).filter_by(username="admin").one().is_active
    svc.set_user_status(anh, binh.user_id, False)
    assert svc.reset_user_password(anh, binh.user_id)
    svc.set_user_status(anh, _session(db, "chi").user_id, True)


def test_system_admin_is_never_locked_or_demoted(db):
    boss = _session(db, "admin")
    anh = _promoted(db)
    svc.set_user_status(boss, anh.user_id, False)
    svc.set_user_status(boss, anh.user_id, True)
    assert svc.reset_user_password(boss, anh.user_id)
    demo = SessionUser(user_id=0, username="demo.admin", email="d@x", role="Admin")
    with pytest.raises(ValueError, match="được bảo vệ"):
        svc.set_user_role(demo, boss.user_id, "User")  # còn admin khác nên không vướng "admin cuối cùng", nhưng admin hệ thống vẫn không bị thu quyền
    svc.set_user_role(boss, anh.user_id, "User")


def test_list_users_reports_system_admin_flag(db):
    rows, _ = svc.list_users(_session(db, "admin"))
    assert {r["username"]: r["is_system_admin"] for r in rows} == {"admin": True, "anh": False, "binh": False, "chi": False}


# ---------- xóa tài khoản ----------
def _seed_user_data(db, username):
    """Một mẫu + một lượt phân tích, một mã đặt lại mật khẩu và một dòng nhật ký của `username`."""
    _predict(db, username, "angry", NOW)
    with db() as s:
        uid = s.query(User).filter_by(username=username).one().user_id
        s.add(PasswordReset(user_id=uid, token_hash="x", expires_at=NOW + timedelta(minutes=15)))
        s.add(SystemLog(level="INFO", service="auth", message=f"Đăng nhập: {username}", user_id=uid))
        s.commit()
    return uid


def test_delete_user_removes_account_and_its_data_but_keeps_log_lines(db):
    admin = _session(db, "admin")
    uid = _seed_user_data(db, "anh")
    other = _seed_user_data(db, "binh")
    summary = svc.delete_user(admin, uid)
    assert summary["username"] == "anh" and summary["audio_files"] == 1 and summary["predictions"] == 1
    with db() as s:
        assert s.get(User, uid) is None and s.get(User, other) is not None
        assert s.query(AudioFile).filter_by(user_id=uid).count() == 0 and s.query(AudioFile).filter_by(user_id=other).count() == 1
        assert s.query(Prediction).count() == 1 and s.query(PasswordReset).filter_by(user_id=uid).count() == 0
        kept = s.query(SystemLog).filter(SystemLog.message == "Đăng nhập: anh").one()
        assert kept.user_id is None  # dòng nhật ký còn nguyên, chỉ bỏ liên kết tới tài khoản đã xóa
        warning = s.query(SystemLog).filter(SystemLog.level == "WARNING").one()
        assert "admin xóa tài khoản anh (1 mẫu âm thanh, 1 lượt phân tích)" in warning.message and warning.user_id == admin.user_id
    with pytest.raises(ValueError, match="Không tìm thấy"):
        svc.delete_user(admin, uid)


def test_delete_user_works_for_a_user_without_any_data(db):
    assert svc.delete_user(_session(db, "admin"), _session(db, "chi").user_id)["audio_files"] == 0
    with db() as s:
        assert s.query(User).count() == 3


def test_delete_user_guards(db):
    boss = _session(db, "admin")
    anh = _promoted(db)
    with pytest.raises(ValueError, match="tự xóa"):
        svc.delete_user(anh, anh.user_id)
    with pytest.raises(ValueError, match="tự xóa"):
        svc.delete_user(boss, boss.user_id)
    with pytest.raises(ValueError, match="được bảo vệ"):
        svc.delete_user(anh, boss.user_id)  # admin được cấp lên không xóa được admin hệ thống
    demo = SessionUser(user_id=0, username="demo.admin", email="d@x", role="Admin")
    with pytest.raises(ValueError, match="được bảo vệ"):
        svc.delete_user(demo, boss.user_id)  # admin hệ thống cũng không bị ai xóa, kể cả phiên thử
    with db() as s:
        assert s.query(User).count() == 4


def test_promoted_admin_can_delete_users_and_other_admins(db):
    anh = _promoted(db)
    binh = _promoted(db, "binh")
    svc.delete_user(anh, _session(db, "chi").user_id)
    svc.delete_user(anh, binh.user_id)
    with db() as s:
        assert sorted(u.username for u in s.query(User)) == ["admin", "anh"]
