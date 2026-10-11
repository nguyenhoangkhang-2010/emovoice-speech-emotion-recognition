# Tạo bảng từ metadata của các model. Chưa gọi khi khởi động app trong giai đoạn skeleton.
# TODO: thay bằng Alembic migration trước khi chuyển sang PostgreSQL thật (báo cáo Mục 2.4).
from db.base import Base
from db.session import engine
import models  # noqa: F401  (đăng ký toàn bộ bảng vào Base.metadata)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
