# Bảng system_logs (BỔ SUNG, chưa có trong báo cáo Mục 2.4): nhật ký sự kiện hệ thống cho UC06, trang admin Nhật ký hệ thống.
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.user import User


class SystemLog(Base):
    __tablename__ = "system_logs"
    __table_args__ = (CheckConstraint("level IN ('INFO', 'WARNING', 'ERROR')", name="ck_system_logs_level"),)

    log_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    level: Mapped[str] = mapped_column(String(10), index=True)
    service: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    user: Mapped[Optional["User"]] = relationship(back_populates="system_logs")
