# Cho phép `import core, services, ml, ui` khi chạy `python -m pytest tests` từ thư mục emovoice/.
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(autouse=True)
def audit_db(monkeypatch):
    """Mọi test đều ghi nhật ký (services.audit_service) vào một CSDL SQLite trong bộ nhớ riêng, KHÔNG bao giờ vào CSDL thật của máy.
    Test nào cần đọc lại các dòng đã ghi thì nhận fixture này (trả về hàm mở phiên, dùng như `with audit_db() as s:`)."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    import models  # noqa: F401  (đăng ký bảng vào Base.metadata)
    from db.base import Base
    from services import audit_service

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False)

    @contextmanager
    def session():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(audit_service, "get_session", session)
    return session
