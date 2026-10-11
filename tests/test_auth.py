# UC01 đăng ký / đăng nhập / đăng xuất (báo cáo Bảng 2.3). Test ID: TC-UC01-* trong docs/test-plan.md.
import pytest


@pytest.mark.skip(reason="TODO UC01: cài auth_service.register rồi kiểm tra trùng username/email và mật khẩu được băm bcrypt (không lưu mật khẩu thô)")
def test_register_hashes_password_and_rejects_duplicates():
    ...


@pytest.mark.skip(reason="TODO UC01: cài auth_service.login rồi kiểm tra sai mật khẩu -> ValueError, tài khoản is_active=False -> bị từ chối")
def test_login_rejects_wrong_password_and_locked_account():
    ...
