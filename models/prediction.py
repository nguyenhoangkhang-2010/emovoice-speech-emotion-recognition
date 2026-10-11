# Bảng predictions (UC04, UC05): mỗi lượt suy luận; emotion_id là nhãn có xác suất cao nhất.
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.audio_file import AudioFile
    from models.emotion import Emotion
    from models.ml_model import MLModel
    from models.prediction_score import PredictionScore


class Prediction(Base):
    __tablename__ = "predictions"

    prediction_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    audio_id: Mapped[int] = mapped_column(ForeignKey("audio_files.audio_id"), index=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("models.model_id"))
    emotion_id: Mapped[int] = mapped_column(ForeignKey("emotions.emotion_id"), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    heatmap_path: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    audio: Mapped["AudioFile"] = relationship(back_populates="predictions")
    model: Mapped["MLModel"] = relationship(back_populates="predictions")
    emotion: Mapped["Emotion"] = relationship(back_populates="predictions")
    scores: Mapped[List["PredictionScore"]] = relationship(back_populates="prediction", cascade="all, delete-orphan")
