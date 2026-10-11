# Bảng password_resets (BỔ SUNG, chưa có trong báo cáo Mục 2.4): mã đặt lại mật khẩu cho UC01 "Quên mật khẩu" (đề cương tuần 9).
# Chỉ lưu token_hash (SHA-256), không lưu mã thô; hết hạn sau PASSWORD_RESET_TTL_MINUTES; used_at đánh dấu đã dùng.
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.user import User


class PasswordReset(Base):
    __tablename__ = "password_resets"

    reset_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(128), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="password_resets")
