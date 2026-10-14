# Dữ liệu ban đầu (db.seed) và băm mật khẩu bcrypt (core.security). SQLite trong bộ nhớ, không đụng DB thật.
from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import db.session
import models  # noqa: F401  (đăng ký bảng vào Base.metadata)
from core.config import settings
from core.security import BCRYPT_MAX_BYTES, hash_password, verify_password
from db import seed as seed_module
from db.base import Base
from models.emotion import Emotion
from models.ml_model import MLModel
from models.user import User


@pytest.fixture()
def factory(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    make = sessionmaker(bind=engine, autoflush=False)

    @contextmanager
    def fake_get_session():
        session = make()
        try:
            yield session
        finally:
            session.close()

    monkeypatch.setattr(db.session, "get_session", fake_get_session)
    return fake_get_session


def test_seed_loads_emotions_and_admin_only(factory):
    seed_module.seed()
    with factory() as s:
        assert [e.name for e in s.scalars(select(Emotion).order_by(Emotion.emotion_id))] == [row["name"] for row in seed_module.SEED_EMOTIONS]
        assert s.query(MLModel).count() == 0  # bảng models để trống: mô hình được ghi vào khi đăng ký / đánh giá thật
        admin = s.query(User).one()
        assert admin.username == settings.admin_username and admin.role == "Admin" and admin.is_active
        assert admin.password != settings.admin_password and verify_password(settings.admin_password, admin.password)


def test_seed_is_idempotent(factory):
    seed_module.seed()
    seed_module.seed()
    with factory() as s:
        assert s.query(Emotion).count() == 8
        assert s.query(MLModel).count() == 0
        assert s.query(User).count() == 1


def test_seed_keeps_existing_admin_password(factory):
    seed_module.seed()
    with factory() as s:
        s.query(User).one().password = hash_password("mat-khau-da-doi-1")
        s.commit()
    seed_module.seed()
    with factory() as s:
        assert verify_password("mat-khau-da-doi-1", s.query(User).one().password)  # seed không ghi đè mật khẩu đã đổi


def test_password_hash_roundtrip():
    hashed = hash_password("Mật khẩu có dấu 123")
    assert hashed.startswith("$2") and "Mật khẩu" not in hashed
    assert verify_password("Mật khẩu có dấu 123", hashed)
    assert not verify_password("sai", hashed)
    assert hash_password("a1234567") != hash_password("a1234567")  # mỗi lần băm dùng salt khác nhau


def test_password_rejects_over_bcrypt_limit_and_bad_hash():
    with pytest.raises(ValueError):
        hash_password("x" * (BCRYPT_MAX_BYTES + 1))
    assert verify_password("x" * (BCRYPT_MAX_BYTES + 1), hash_password("x" * BCRYPT_MAX_BYTES)) is False
    assert verify_password("abc", "khong-phai-hash") is False
