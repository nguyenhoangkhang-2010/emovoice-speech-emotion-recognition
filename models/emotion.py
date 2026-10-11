# Bảng emotions: 8 nhãn cảm xúc. emotion_id trùng chỉ số lớp của mô hình (0-7), không tự tăng.
from typing import TYPE_CHECKING, List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.prediction import Prediction
    from models.prediction_score import PredictionScore


class Emotion(Base):
    __tablename__ = "emotions"

    emotion_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(30), unique=True)
    name_vi: Mapped[str] = mapped_column(String(50))

    predictions: Mapped[List["Prediction"]] = relationship(back_populates="emotion")
    scores: Mapped[List["PredictionScore"]] = relationship(back_populates="emotion")
