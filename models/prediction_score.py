# Bảng prediction_scores (UC04): xác suất 8 lớp cho mỗi lượt dự đoán; khóa chính kép (prediction_id, emotion_id).
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.emotion import Emotion
    from models.prediction import Prediction


class PredictionScore(Base):
    __tablename__ = "prediction_scores"
    __table_args__ = (CheckConstraint("probability >= 0 AND probability <= 1", name="ck_prediction_scores_prob"),)

    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.prediction_id"), primary_key=True)
    emotion_id: Mapped[int] = mapped_column(ForeignKey("emotions.emotion_id"), primary_key=True)
    probability: Mapped[float] = mapped_column(Float)

    prediction: Mapped["Prediction"] = relationship(back_populates="scores")
    emotion: Mapped["Emotion"] = relationship(back_populates="scores")
