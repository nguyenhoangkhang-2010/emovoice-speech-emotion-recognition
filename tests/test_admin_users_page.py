# Popup "Thêm tài khoản" (trang Quản lý người dùng): xử lý nhập liệu và hiển thị kết quả.
import gradio as gr
import pytest
from sqlalchemy.exc import OperationalError

from core.session import SessionUser
from ui import i18n_vi as T
from ui.pages import admin_users

ADMIN = SessionUser(user_id=1, username="admin", email="a@x.vn", role="Admin")


def test_requires_admin():
    with pytest.raises(gr.Error):
        admin_users.create_user_action(None, "ten", "a@x.vn", "", "User")
    with pytest.raises(gr.Error):
        admin_users.create_user_action(SessionUser(user_id=2, username="u", email="u@x", role="User"), "ten", "a@x.vn", "", "User")


def test_blank_required_fields_ask_to_fill_in(monkeypatch):
    called = []
    monkeypatch.setattr(admin_users.admin_service, "create_user", lambda *a, **k: called.append(a))
    html, ok = admin_users.create_user_action(ADMIN, "  ", "a@x.vn", "", "User")
    assert ok is False and T.MSG_FILL_ALL in html and called == []  # chưa đủ thông tin thì không gọi dịch vụ
    assert admin_users.create_user_action(ADMIN, "ten", "", "", "User")[1] is False


def test_success_shows_temp_password_once(monkeypatch):
    monkeypatch.setattr(admin_users.admin_service, "create_user", lambda session, u, e, role, name: {"username": "moi", "temp_password": "Abc123xyz789"})
    html, ok = admin_users.create_user_action(ADMIN, "moi", "moi@x.vn", "Họ Tên", "Admin")
    assert ok is True and "Đã tạo tài khoản moi" in html and "<code>Abc123xyz789</code>" in html and "chỉ hiện một lần" in html and "Mật khẩu tạm" in html


def test_service_errors_are_shown_verbatim_and_db_errors_generically(monkeypatch):
    def invalid(*args):
        raise ValueError("Tên đăng nhập hoặc email đã được sử dụng.")

    monkeypatch.setattr(admin_users.admin_service, "create_user", invalid)
    html, ok = admin_users.create_user_action(ADMIN, "moi", "moi@x.vn", "", "User")
    assert ok is False and "đã được sử dụng" in html

    def down(*args):
        raise OperationalError("insert", {}, Exception("connection refused"))

    monkeypatch.setattr(admin_users.admin_service, "create_user", down)
    html, ok = admin_users.create_user_action(ADMIN, "moi", "moi@x.vn", "", "User")
    assert ok is False and T.MSG_DB_ERROR in html and "connection refused" not in html  # không lộ chi tiết kết nối


def test_missing_role_defaults_to_plain_user(monkeypatch):
    seen = {}
    monkeypatch.setattr(admin_users.admin_service, "create_user", lambda session, u, e, role, name: seen.update(role=role, name=name) or {"username": u, "temp_password": "x"})
    admin_users.create_user_action(ADMIN, "moi", "moi@x.vn", None, None)
    assert seen == {"role": "User", "name": ""}
