# SessionUser lưu trong gr.State sau đăng nhập; require_login/require_admin là lớp bảo vệ phía server (UC01, UC06).
# Ẩn mục menu trên giao diện chỉ là UX: MỌI handler admin phải gọi require_admin.
from dataclasses import dataclass
from typing import Optional

ROLE_USER = "User"
ROLE_ADMIN = "Admin"


class PermissionDenied(Exception):
    """Phiên chưa đăng nhập hoặc không đủ quyền."""


@dataclass(frozen=True)
class SessionUser:
    user_id: int
    username: str
    email: str
    role: str = ROLE_USER
    display_name: str = ""

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN

    @property
    def name(self) -> str:
        return self.display_name or self.username


def require_login(session: Optional[SessionUser]) -> SessionUser:
    if session is None:
        raise PermissionDenied("Vui lòng đăng nhập để tiếp tục.")
    return session


def require_admin(session: Optional[SessionUser]) -> SessionUser:
    user = require_login(session)
    if not user.is_admin:
        raise PermissionDenied("Chức năng này chỉ dành cho Quản trị viên.")
    return user
