# UC06 phân quyền: người thường không vào được chức năng admin (lớp bảo vệ phía server, không chỉ ẩn menu).
import pytest

from core.session import PermissionDenied, SessionUser, require_admin, require_login


def test_require_admin_blocks_user_and_anonymous():
    user = SessionUser(user_id=2, username="u", email="u@x.vn", role="User")
    admin = SessionUser(user_id=1, username="a", email="a@x.vn", role="Admin")
    assert require_admin(admin) is admin
    assert require_login(user) is user
    with pytest.raises(PermissionDenied):
        require_admin(user)
    with pytest.raises(PermissionDenied):
        require_admin(None)


@pytest.mark.skip(reason="TODO UC06: khi admin_service được cài đặt, kiểm tra mọi hàm admin_service.* ném PermissionDenied với session User/None")
def test_admin_service_functions_reject_non_admin():
    ...
