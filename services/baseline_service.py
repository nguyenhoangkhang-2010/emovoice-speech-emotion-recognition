# Chạy thêm baseline Random Forest trên cùng một tệp âm thanh để SO SÁNH với mô hình chính (không thay thế, không lưu vào lịch sử).
# Baseline lấy từ bảng models (đăng ký bằng `python -m ml.register_baseline`); nó không có attention nên không có XAI.
import logging
import time
from pathlib import Path
from typing import Any, Dict

from services import model_service

logger = logging.getLogger(__name__)

MSG_NOT_REGISTERED = "Chưa đăng ký baseline Random Forest. Quản trị viên cần chạy `python -m ml.register_baseline --checkpoint <tệp .pkl>`."
MSG_MISSING_FILE = "Không thấy tệp của baseline Random Forest ({name}): {path}"
MSG_REGISTRY_DOWN = "Chưa đọc được danh sách mô hình để tìm baseline."
MSG_LOAD_FAILED = "Không chạy được baseline Random Forest. Xem nhật ký máy chủ để biết chi tiết."


class BaselineNotReady(Exception):
    """Không chạy được baseline (chưa đăng ký, thiếu tệp, lỗi nạp). Thông báo là tiếng Việt, hiện thẳng cho người dùng."""


def run_random_forest(audio_path: str) -> Dict[str, Any]:
    """{'name', 'probs' [8], 'latency_ms', 'accuracy', 'macro_f1'} cho một tệp âm thanh; BaselineNotReady nếu không chạy được."""
    from ml import baseline, preprocess

    try:
        entry = model_service.baseline_model("random_forest")
    except model_service.RegistryUnavailable:
        raise BaselineNotReady(MSG_REGISTRY_DOWN)
    if entry is None:
        raise BaselineNotReady(MSG_NOT_REGISTERED)
    checkpoint = entry.get("checkpoint_path") or ""
    if not checkpoint or not Path(checkpoint).exists():
        raise BaselineNotReady(MSG_MISSING_FILE.format(name=entry["name"], path=checkpoint or "—"))
    started = time.perf_counter()
    try:
        features = preprocess.features_212_for_file(audio_path)
        probs = baseline.predict_probs(features, checkpoint)
    except Exception:
        logger.exception("Baseline Random Forest lỗi")
        raise BaselineNotReady(MSG_LOAD_FAILED)
    return {
        "name": entry["name"],
        "probs": probs,
        "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        "accuracy": entry["accuracy"],
        "macro_f1": entry["macro_f1"],
    }
