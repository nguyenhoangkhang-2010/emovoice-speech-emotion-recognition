# UC04 (báo cáo Bảng 2.6): nạp mô hình một lần, suy luận, ngưỡng độ tin cậy thấp, lưu predictions + prediction_scores.
import numpy as np


def load_model_once() -> None:
    raise NotImplementedError("TODO UC04: gọi ml.inference.load_model một lần, ghi trạng thái nạp cho system_status_service")


def run_inference(waveform: np.ndarray):
    raise NotImplementedError("TODO UC04: trả (probs [8], attn_weights [149]) từ ml.inference.predict; đo thời gian (mục tiêu < 1,5 s, báo cáo Mục 2.1.2)")


def is_low_confidence(probs: np.ndarray) -> bool:
    raise NotImplementedError("TODO UC04: True nếu mọi xác suất < LOW_CONFIDENCE_THRESHOLD (0,30) -> giao diện hiện cảnh báo 'độ tin cậy thấp'")


def save_prediction(session, audio_id: int, probs: np.ndarray, heatmap_path: str):
    raise NotImplementedError("TODO UC04/UC05: ghi predictions và 8 dòng prediction_scores trong một transaction")
