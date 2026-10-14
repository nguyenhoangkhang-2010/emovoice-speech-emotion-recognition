# Bảng users (UC01, UC06). Cột password lưu hash bcrypt, không lưu mật khẩu thô.
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from db.base import Base

if TYPE_CHECKING:
    from models.audio_file import AudioFile
    from models.password_reset import PasswordReset
    from models.system_log import SystemLog

ROLE_USER = "User"
ROLE_ADMIN = "Admin"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('User', 'Admin')", name="ck_users_role"),)

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # họ tên hiển thị; trống thì giao diện dùng username
    password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(10), default=ROLE_USER, server_default=ROLE_USER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=expression.true())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    audio_files: Mapped[List["AudioFile"]] = relationship(back_populates="user")
    system_logs: Mapped[List["SystemLog"]] = relationship(back_populates="user")
    password_resets: Mapped[List["PasswordReset"]] = relationship(back_populates="user")
