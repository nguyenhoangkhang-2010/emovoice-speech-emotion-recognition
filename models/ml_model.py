# Bảng models (trang Mô hình & hiệu năng, admin Quản lý mô hình): các mô hình đã thử nghiệm; chỉ 1 dòng is_active=true.
# Lớp tên MLModel để không trùng khái niệm "model" của SQLAlchemy; tên bảng vẫn là "models".
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Float, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from db.base import Base

if TYPE_CHECKING:
    from models.prediction import Prediction


class MLModel(Base):
    __tablename__ = "models"
    __table_args__ = (
        Index(
            "uq_models_single_active",
            "is_active",
            unique=True,
            sqlite_where=text("is_active = 1"),
            postgresql_where=text("is_active"),
        ),
    )

    model_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    model_type: Mapped[str] = mapped_column(String(50))
    accuracy: Mapped[Optional[float]] = mapped_column(Float)  # %
    f1_score: Mapped[Optional[float]] = mapped_column(Float)  # % (macro)
    size_mb: Mapped[Optional[float]] = mapped_column(Float)  # MiB (checkpoint)
    inference_time: Mapped[Optional[float]] = mapped_column(Float)  # ms/mẫu 3 s (báo cáo Bảng 5.4)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, server_default=expression.false())

    predictions: Mapped[List["Prediction"]] = relationship(back_populates="model")
