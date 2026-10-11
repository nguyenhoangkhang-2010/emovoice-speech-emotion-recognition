# UC06 (báo cáo Bảng 2.8): thống kê, quản lý tài khoản, nhật ký, dữ liệu âm thanh. MỌI hàm nhận session và gọi require_admin ở dòng đầu.
from typing import Optional

from core.session import SessionUser


def get_stats(session: SessionUser):
    raise NotImplementedError("TODO UC06: tổng lượt phân tích, số tài khoản, phân bố 8 cảm xúc, lượt theo ngày (7 ngày); require_admin")


def list_users(session: SessionUser, page: int = 1, page_size: int = 10, q: Optional[str] = None):
    raise NotImplementedError("TODO UC06: danh sách tài khoản có tìm kiếm + phân trang; require_admin")


def set_user_status(session: SessionUser, user_id: int, is_active: bool) -> None:
    raise NotImplementedError("TODO UC06: khóa/mở tài khoản, không cho Admin tự khóa chính mình, ghi system_logs; require_admin")


def list_logs(session: SessionUser, page: int = 1, page_size: int = 10, level: Optional[str] = None, on_date: Optional[str] = None, q: Optional[str] = None):
    raise NotImplementedError("TODO UC06: nhật ký hệ thống lọc theo mức, ngày, từ khóa; require_admin")


def list_all_audio(session: SessionUser, page: int = 1, page_size: int = 10, q: Optional[str] = None, emotion: Optional[str] = None):
    raise NotImplementedError("TODO admin_audio (đề cương: 'quản lý dữ liệu'): mẫu âm thanh của mọi người dùng; require_admin")


def delete_audio(session: SessionUser, audio_id: int) -> None:
    raise NotImplementedError("TODO admin_audio: xóa mẫu + tệp + dòng liên quan, ghi system_logs; require_admin")
