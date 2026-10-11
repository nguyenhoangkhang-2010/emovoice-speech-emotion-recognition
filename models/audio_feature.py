# Bảng audio_features (UC03/UC07): đặc trưng sau tiền xử lý. 1-1 với audio_files (audio_id vừa là PK vừa là FK).
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.audio_file import AudioFile


class AudioFeature(Base):
    __tablename__ = "audio_features"

    audio_id: Mapped[int] = mapped_column(ForeignKey("audio_files.audio_id"), primary_key=True)
    trimmed_duration: Mapped[Optional[float]] = mapped_column(Float)
    mel_image_path: Mapped[Optional[str]] = mapped_column(String(500))
    mfcc_mean: Mapped[Optional[float]] = mapped_column(Float)
    f0_mean: Mapped[Optional[float]] = mapped_column(Float)
    voiced_ratio: Mapped[Optional[float]] = mapped_column(Float)
    rms_mean: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    audio: Mapped["AudioFile"] = relationship(back_populates="features")
