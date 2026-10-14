# Mỗi trang là một module có build(session_state) -> dict component. Module trang (trừ login) khai báo thêm:
#   NAME, LABEL, GROUP ("analysis"|"account"|"admin"), ADMIN_ONLY, EXTRA (chỉ hiện khi ENABLE_ADMIN_EXTRA_PAGES=1).
# Khóa tùy chọn trong dict trả về: "load_fn"/"load_outputs" (nạp dữ liệu khi vào trang), "goto_<page>" (nút chuyển trang, ui/layout nối sự kiện).
import gradio as gr

from core.session import PermissionDenied, SessionUser, require_admin, require_login


def guard_login(session) -> SessionUser:
    try:
        return require_login(session)
    except PermissionDenied as exc:
        raise gr.Error(str(exc))


def guard_admin(session) -> SessionUser:
    """Lớp bảo vệ phía server cho MỌI handler admin (ẩn menu chỉ là UX)."""
    try:
        return require_admin(session)
    except PermissionDenied as exc:
        raise gr.Error(str(exc))
