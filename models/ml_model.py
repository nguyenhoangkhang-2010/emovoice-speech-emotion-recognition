# Bảng models (trang Mô hình & hiệu năng, admin Quản lý mô hình): các mô hình đã thử nghiệm; chỉ 1 dòng is_active=true.
# Lớp tên MLModel để không trùng khái niệm "model" của SQLAlchemy; tên bảng vẫn là "models".
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, Index, String, func, text
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
    # Thông tin đo thật khi đăng ký mô hình (python -m ml.register_model); không nhập tay.
    checkpoint_path: Mapped[Optional[str]] = mapped_column(String(500))  # đường dẫn tuyệt đối tới tệp trọng số
    params_total: Mapped[Optional[int]] = mapped_column()
    params_trainable: Mapped[Optional[int]] = mapped_column()
    eval_dataset: Mapped[Optional[str]] = mapped_column(String(200))  # mô tả tập kiểm thử đã dùng
    eval_samples: Mapped[Optional[int]] = mapped_column()
    latency_device: Mapped[Optional[str]] = mapped_column(String(50))  # cpu / cuda: độ trễ chỉ so sánh được khi cùng thiết bị
    evaluated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # chỉ số từng lớp, ma trận nhầm lẫn, cấu hình đo
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    predictions: Mapped[List["Prediction"]] = relationship(back_populates="model")
