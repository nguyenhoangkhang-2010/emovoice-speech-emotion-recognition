# Bảng audio_files (UC02): tệp người dùng tải lên/thu âm. users 1-n audio_files.
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.audio_feature import AudioFeature
    from models.prediction import Prediction
    from models.user import User


class AudioFile(Base):
    __tablename__ = "audio_files"

    audio_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    duration: Mapped[float] = mapped_column(Float)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="audio_files")
    features: Mapped[Optional["AudioFeature"]] = relationship(
        back_populates="audio", uselist=False, cascade="all, delete-orphan"
    )
    predictions: Mapped[List["Prediction"]] = relationship(back_populates="audio")
