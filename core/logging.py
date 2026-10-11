# Ghi nhật ký hệ thống ra logs/ và bảng system_logs (UC06, trang admin Nhật ký hệ thống).
# TODO: cấu hình logging chuẩn + log_event ghi DB mà không làm hỏng request nếu ghi lỗi.
def setup_logging() -> None:
    raise NotImplementedError("TODO UC06: cấu hình logging ra settings.log_dir")


def log_event(level: str, service: str, message: str, user_id: int | None = None) -> None:
    raise NotImplementedError("TODO UC06: ghi file log và dòng system_logs (level INFO/WARNING/ERROR)")
