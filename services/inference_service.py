# UC04 (báo cáo Bảng 2.6): nạp mô hình một lần, suy luận, ngưỡng độ tin cậy thấp, lưu predictions + prediction_scores.
# Mô hình dùng để suy luận là mô hình ĐANG DÙNG trong bảng models (đường dẫn checkpoint ghi lúc đăng ký);
# chưa có thì dùng MODEL_CHECKPOINT_PATH trong .env nếu tệp tồn tại.
import time
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

from core.config import settings
from services import audit_service, model_service


class ModelNotReady(Exception):
    """Chưa có mô hình nào dùng được để suy luận (chưa đăng ký / thiếu tệp checkpoint)."""


_state = {"name": None, "path": None, "model_key": None, "last_latency_ms": None}


def _resolve_checkpoint() -> Tuple[str, str, Optional[str]]:
    """(tên hiển thị, đường dẫn checkpoint, key trong bảng models hoặc None nếu dùng MODEL_CHECKPOINT_PATH) của mô hình sẽ dùng."""
    try:
        active = model_service.active_model()
    except model_service.RegistryUnavailable:
        active = None  # DB chưa sẵn sàng: vẫn cho phép chạy bằng MODEL_CHECKPOINT_PATH
    if active and active.get("checkpoint_path"):
        path = Path(active["checkpoint_path"])
        if not path.exists():
            raise ModelNotReady(f"Không thấy tệp checkpoint của mô hình đang dùng ({active['name']}): {path}")
        return active["name"], str(path), active["key"]
    fallback = settings.checkpoint_path
    if fallback.exists():
        return fallback.stem, str(fallback), None
    raise ModelNotReady("Chưa có mô hình đang dùng. Quản trị viên cần chạy `python -m ml.register_model --checkpoint <tệp .pt> --activate`.")


def load_model_once() -> None:
    """Nạp mô hình vào bộ nhớ (idempotent). Ghi tên/đường dẫn để trang trạng thái hệ thống đọc."""
    from ml import inference

    name, path, key = _resolve_checkpoint()
    inference.load_model(path)
    _state.update(name=name, path=path, model_key=key)


def run_inference(waveform: np.ndarray):
    """(probs [8], attn_weights [149]). Thời gian suy luận lưu vào status()['last_latency_ms'] (mục tiêu < 1,5 s, báo cáo Mục 2.1.2)."""
    from ml import inference

    name, path, key = _resolve_checkpoint()
    info = inference.loaded_info()
    first_load = not (info["loaded"] and info["path"] == path)
    started = time.perf_counter()
    _, probs, attn = inference.predict(waveform, path)
    _state.update(name=name, path=path, model_key=key, last_latency_ms=round((time.perf_counter() - started) * 1000, 1))
    if first_load:  # lần đầu sau khi khởi động (hoặc khi đổi mô hình): ghi một dòng để admin biết mô hình đã nạp vào bộ nhớ
        audit_service.log("INFO", "model", f"Nạp mô hình {name} lên {inference.loaded_info()['device']}, suy luận lần đầu {_state['last_latency_ms']:.0f} ms")
    return probs, attn


def status() -> dict:
    """{'name', 'path', 'last_latency_ms', 'loaded', 'device'} cho trang trạng thái hệ thống."""
    from ml import inference

    return {**_state, **inference.loaded_info()}


def last_model_name() -> Optional[str]:
    """Tên mô hình chính của lượt suy luận gần nhất (để ghi nhãn trên bảng so sánh với baseline)."""
    return _state["name"]


def last_latency_ms() -> Optional[float]:
    """Thời gian suy luận (ms) của lượt phân tích gần nhất trong tiến trình này; None nếu chưa có lượt nào."""
    return _state["last_latency_ms"]


def is_low_confidence(probs: np.ndarray, threshold: Optional[float] = None) -> bool:
    """True nếu mọi xác suất đều dưới ngưỡng (mặc định LOW_CONFIDENCE_THRESHOLD = 0,30)."""
    limit = settings.low_confidence_threshold if threshold is None else threshold
    return bool(np.max(np.asarray(probs, dtype=np.float64)) < limit)


def save_prediction(session, audio_id: int, probs: np.ndarray, heatmap_path: Optional[str]) -> Optional[int]:
    """Ghi predictions và 8 dòng prediction_scores trong một transaction; trả prediction_id.
    Dùng mô hình của lần run_inference gần nhất; trả None nếu lần đó chạy bằng MODEL_CHECKPOINT_PATH (chưa đăng ký nên không có model_id)."""
    from core.session import require_login
    from db.session import get_session
    from models.audio_file import AudioFile
    from models.prediction import Prediction
    from models.prediction_score import PredictionScore

    user = require_login(session)
    values = np.clip(np.asarray(probs, dtype=np.float64).reshape(-1), 0.0, 1.0)  # softmax float32 có thể lệch 1e-7 ra ngoài [0,1]
    if len(values) != 8:
        raise ValueError("Cần đúng 8 xác suất cho 8 nhãn cảm xúc.")
    if _state["model_key"] is None:
        return None
    top = int(np.argmax(values))
    with get_session() as db:
        audio = db.get(AudioFile, audio_id)
        if audio is None or (audio.user_id != user.user_id and not user.is_admin):
            raise ValueError("Không tìm thấy tệp âm thanh của bạn.")
        prediction = Prediction(audio_id=audio_id, model_id=int(_state["model_key"]), emotion_id=top, confidence=float(values[top]), heatmap_path=heatmap_path)
        prediction.scores = [PredictionScore(emotion_id=i, probability=float(p)) for i, p in enumerate(values)]
        db.add(prediction)
        db.commit()
        return prediction.prediction_id
