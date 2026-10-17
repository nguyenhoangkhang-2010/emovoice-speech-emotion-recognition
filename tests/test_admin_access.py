# UC06 phân quyền: người thường không vào được chức năng admin (lớp bảo vệ phía server, không chỉ ẩn menu).
import inspect

import pytest

from core.session import PermissionDenied, SessionUser, require_admin, require_login
from services import admin_service


def test_require_admin_blocks_user_and_anonymous():
    user = SessionUser(user_id=2, username="u", email="u@x.vn", role="User")
    admin = SessionUser(user_id=1, username="a", email="a@x.vn", role="Admin")
    assert require_admin(admin) is admin
    assert require_login(user) is user
    with pytest.raises(PermissionDenied):
        require_admin(user)
    with pytest.raises(PermissionDenied):
        require_admin(None)


def _public_functions():
    return [f for name, f in inspect.getmembers(admin_service, inspect.isfunction) if f.__module__ == admin_service.__name__ and not name.startswith("_")]


def test_admin_service_functions_reject_non_admin():
    """Tự quét MỌI hàm công khai của admin_service: hàm mới thêm sau này mà quên require_admin sẽ làm test này đỏ."""
    functions = _public_functions()
    assert len(functions) >= 7
    user = SessionUser(user_id=2, username="u", email="u@x.vn", role="User")
    for func in functions:
        required = [p for p in list(inspect.signature(func).parameters.values())[1:] if p.default is inspect.Parameter.empty]
        for who in (user, None):
            with pytest.raises(PermissionDenied, match=""):
                func(who, *([1] * len(required)))
