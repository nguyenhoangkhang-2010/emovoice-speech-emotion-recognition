# Tạo nhanh bảng từ metadata của các model (dùng cho thử nghiệm nhanh với SQLite). Với PostgreSQL hãy dùng Alembic: `alembic upgrade head`.
from db.base import Base
from db.session import engine
import models  # noqa: F401  (đăng ký toàn bộ bảng vào Base.metadata)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
