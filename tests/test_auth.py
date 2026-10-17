# UC01 đăng ký / đăng nhập / đăng xuất (báo cáo Bảng 2.3). Test ID: TC-UC01-* trong docs/test-plan.md. SQLite trong bộ nhớ.
from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401  (đăng ký bảng vào Base.metadata)
from core.security import verify_password
from core.session import SessionUser
from db.base import Base
from models.system_log import SystemLog
from models.user import User
from services import auth_service as svc


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
    svc._failures.clear()
    return fake_get_session


def _register(username="anh", email="An@Example.com", password="matkhau123"):
    return svc.register(username, email, password, password)


def _logs(db, level=None):
    with db() as s:
        rows = s.query(SystemLog).all()
        return [r.message for r in rows if level is None or r.level == level]


def test_register_hashes_password_and_returns_session(db):
    session = _register()
    assert isinstance(session, SessionUser) and session.role == "User" and session.email == "an@example.com" and session.user_id > 0
    with db() as s:
        row = s.query(User).one()
        assert row.password != "matkhau123" and row.password.startswith("$2") and verify_password("matkhau123", row.password)  # bcrypt, không lưu mật khẩu thô
        assert row.is_active is True and row.role == "User"
    assert any("Đăng ký" in m for m in _logs(db, "INFO"))


def test_register_rejects_duplicates_ignoring_case(db):
    _register()
    for username, email in (("ANH", "khac@x.vn"), ("khac", "AN@example.COM"), ("anh", "an@example.com")):
        with pytest.raises(ValueError, match="đã được sử dụng"):
            _register(username, email)
    with db() as s:
        assert s.query(User).count() == 1


@pytest.mark.parametrize(
    "username,email,password,confirm,message",
    [
        ("ab", "a@x.vn", "matkhau123", "matkhau123", "Tên đăng nhập"),
        ("co dau cach", "a@x.vn", "matkhau123", "matkhau123", "Tên đăng nhập"),
        ("hopLe", "khong-phai-email", "matkhau123", "matkhau123", "Email"),
        ("hopLe", "a@x.vn", "ngan", "ngan", "ít nhất 8"),
        ("hopLe", "a@x.vn", "matkhau123", "matkhau456", "không khớp"),
    ],
)
def test_register_validates_input(db, username, email, password, confirm, message):
    with pytest.raises(ValueError, match=message):
        svc.register(username, email, password, confirm)
    with db() as s:
        assert s.query(User).count() == 0


def test_register_rejects_password_over_bcrypt_limit(db):
    with pytest.raises(ValueError, match="72"):
        _register(password="x" * 80)


def test_login_by_username_or_email_case_insensitive(db):
    _register()
    for ident in ("anh", "ANH", "an@example.com", " An@Example.COM "):
        assert svc.login(ident, "matkhau123").username == "anh"
    assert any("Đăng nhập: anh" in m for m in _logs(db, "INFO"))


def test_login_wrong_password_and_unknown_user_share_one_message(db):
    _register()
    with pytest.raises(ValueError) as wrong:
        svc.login("anh", "sai-mat-khau")
    with pytest.raises(ValueError) as unknown:
        svc.login("khong-ton-tai", "matkhau123")
    assert str(wrong.value) == str(unknown.value) == svc.MSG_LOGIN_ERROR  # người ngoài không dò được tên nào tồn tại
    assert len(_logs(db, "WARNING")) == 2
    with pytest.raises(ValueError):
        svc.login("", "")


def test_login_rejects_locked_account_only_with_correct_password(db):
    _register()
    with db() as s:
        s.query(User).one().is_active = False
        s.commit()
    with pytest.raises(ValueError, match="bị khóa"):
        svc.login("anh", "matkhau123")
    with pytest.raises(ValueError) as wrong:
        svc.login("anh", "sai-mat-khau")
    assert str(wrong.value) == svc.MSG_LOGIN_ERROR  # sai mật khẩu thì không lộ tài khoản đang bị khóa


def test_login_blocks_after_too_many_failures_and_success_resets_counter(db):
    _register()
    for _ in range(svc.MAX_FAILED_LOGINS - 1):
        with pytest.raises(ValueError):
            svc.login("anh", "sai")
    assert svc.login("anh", "matkhau123").username == "anh"  # đăng nhập đúng xóa bộ đếm
    for _ in range(svc.MAX_FAILED_LOGINS):
        with pytest.raises(ValueError):
            svc.login("anh", "sai")
    with pytest.raises(ValueError, match="quá nhiều lần"):
        svc.login("anh", "matkhau123")  # đã bị chặn: kể cả mật khẩu đúng cũng không vào được trong cửa sổ thời gian


def test_logout_writes_log_and_ignores_demo_session(db):
    session = _register()
    svc.logout(session)
    svc.logout(SessionUser(user_id=-1, username="demo", email="d@x"))
    svc.logout(None)
    assert [m for m in _logs(db) if "Đăng xuất" in m] == ["Đăng xuất: anh"]


def test_admin_role_is_kept_on_login(db):
    _register()
    with db() as s:
        s.query(User).one().role = "Admin"
        s.commit()
    assert svc.login("anh", "matkhau123").is_admin is True
