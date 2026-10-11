# Import toàn bộ model để đăng ký vào Base.metadata (9 bảng: 7 bảng báo cáo Mục 2.4 + system_logs + password_resets).
from models.audio_feature import AudioFeature
from models.audio_file import AudioFile
from models.emotion import Emotion
from models.ml_model import MLModel
from models.password_reset import PasswordReset
from models.prediction import Prediction
from models.prediction_score import PredictionScore
from models.system_log import SystemLog
from models.user import User

__all__ = [
    "AudioFeature",
    "AudioFile",
    "Emotion",
    "MLModel",
    "PasswordReset",
    "Prediction",
    "PredictionScore",
    "SystemLog",
    "User",
]
