# Trang Tài khoản của tôi (account_service): sửa họ tên / email, đổi mật khẩu. Dùng SQLite trong bộ nhớ, không đụng DB thật.
from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401  (đăng ký bảng vào Base.metadata)
from core.session import PermissionDenied, SessionUser
from db.base import Base
from models.user import User
from services import account_service as svc

DEMO = SessionUser(user_id=-1, username="demo.user", email="demo.user@emovoice.local", display_name="Người dùng (dev)")


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
    monkeypatch.setattr(svc, "hash_password", lambda plain: f"h:{plain}")  # bcrypt thật chưa cài (UC01)
    monkeypatch.setattr(svc, "verify_password", lambda plain, hashed: hashed == f"h:{plain}")
    with fake_get_session() as s:
        s.add_all([User(username="an", email="an@x.vn", password="h:matkhau123", full_name="Nguyễn An"), User(username="binh", email="binh@x.vn", password="h:khac")])
        s.commit()
    return fake_get_session


def _session(db, username):
    with db() as s:
        row = s.query(User).filter_by(username=username).one()
        return SessionUser(user_id=row.user_id, username=row.username, email=row.email, display_name=row.full_name or "")


def test_requires_login():
    with pytest.raises(PermissionDenied):
        svc.update_profile(None, "A", "a@x.vn")
    with pytest.raises(PermissionDenied):
        svc.change_password(None, "a", "b", "b")


def test_update_profile_persists_and_returns_new_session(db):
    an = _session(db, "an")
    updated = svc.update_profile(an, "  Nguyễn   Văn  An ", " AN.NV@X.vn ")
    assert updated.display_name == "Nguyễn Văn An" and updated.email == "an.nv@x.vn" and updated.user_id == an.user_id
    profile = svc.get_profile(updated)
    assert profile["full_name"] == "Nguyễn Văn An" and profile["email"] == "an.nv@x.vn" and profile["username"] == "an"
    assert profile["created_at"] and profile["demo"] is False


@pytest.mark.parametrize("name, email, message", [
    ("", "a@x.vn", svc.MSG_NAME_EMPTY),
    ("   ", "a@x.vn", svc.MSG_NAME_EMPTY),
    ("A" * 101, "a@x.vn", svc.MSG_NAME_LONG),
    ("An", "khong-phai-email", svc.MSG_EMAIL_INVALID),
    ("An", "", svc.MSG_EMAIL_INVALID),
])
def test_update_profile_rejects_bad_input(db, name, email, message):
    with pytest.raises(ValueError, match=message):
        svc.update_profile(_session(db, "an"), name, email)


def test_update_profile_rejects_email_used_by_another_account(db):
    with pytest.raises(ValueError, match=svc.MSG_EMAIL_TAKEN):
        svc.update_profile(_session(db, "an"), "An", "BINH@x.vn")
    assert svc.update_profile(_session(db, "an"), "An", "an@x.vn").email == "an@x.vn"  # giữ nguyên email của chính mình thì được


def test_update_profile_rejects_locked_account(db):
    an = _session(db, "an")
    with db() as s:
        s.query(User).filter_by(username="an").one().is_active = False
        s.commit()
    with pytest.raises(ValueError, match=svc.MSG_NOT_FOUND):
        svc.update_profile(an, "An", "an@x.vn")


def test_demo_session_changes_stay_in_session(db):
    updated = svc.update_profile(DEMO, "Khách thử", "khach@x.vn")
    assert updated.display_name == "Khách thử" and updated.is_demo
    assert svc.get_profile(DEMO)["demo"] is True
    with db() as s:
        assert s.query(User).count() == 2  # không tạo dòng nào trong users


@pytest.mark.parametrize("current, new, confirm, message", [
    ("", "matkhaumoi1", "matkhaumoi1", svc.MSG_PW_FILL),
    ("matkhau123", "matkhaumoi1", "khacnhau123", svc.MSG_PW_MISMATCH),
    ("matkhau123", "ngan", "ngan", svc.MSG_PW_SHORT),
    ("matkhau123", "matkhau123", "matkhau123", svc.MSG_PW_SAME),
    ("saimatkhau", "matkhaumoi1", "matkhaumoi1", svc.MSG_PW_WRONG),
])
def test_change_password_rejections(db, current, new, confirm, message):
    with pytest.raises(ValueError, match=message):
        svc.change_password(_session(db, "an"), current, new, confirm)


def test_change_password_updates_hash(db):
    svc.change_password(_session(db, "an"), "matkhau123", "matkhaumoi1", "matkhaumoi1")
    with db() as s:
        assert s.query(User).filter_by(username="an").one().password == "h:matkhaumoi1"


def test_change_password_rejected_for_demo_session():
    with pytest.raises(ValueError, match=svc.MSG_PW_DEMO):
        svc.change_password(DEMO, "matkhau123", "matkhaumoi1", "matkhaumoi1")
