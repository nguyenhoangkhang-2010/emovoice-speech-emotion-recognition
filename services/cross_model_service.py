# Chạy thêm mô hình CREMA-D 6 nhãn trên cùng đoạn âm thanh để SO SÁNH với mô hình chính RAVDESS 8 nhãn (không thay thế, không lưu vào lịch sử).
# Mô hình lấy từ bảng models (đăng ký bằng `python -m ml.register_model --labels cremad6`); khác bộ nhãn nên chỉ để so sánh.
import logging
import time
from pathlib import Path
from typing import Any, Dict

import numpy as np

from ml.config import CREMAD6_NAMES
from services import model_service

logger = logging.getLogger(__name__)

FAMILY = "cremad6"
MSG_NOT_REGISTERED = "Chưa đăng ký mô hình CREMA-D 6 nhãn. Quản trị viên cần chạy `python -m ml.register_model --labels cremad6`."
MSG_MISSING_FILE = "Không thấy tệp của mô hình CREMA-D ({name}): {path}"
MSG_REGISTRY_DOWN = "Chưa đọc được danh sách mô hình để tìm mô hình CREMA-D."
MSG_LOAD_FAILED = "Không chạy được mô hình CREMA-D 6 nhãn. Xem nhật ký máy chủ để biết chi tiết."


class CrossModelNotReady(Exception):
    """Không chạy được mô hình so sánh (chưa đăng ký, thiếu tệp, lỗi nạp). Thông báo là tiếng Việt, hiện thẳng cho người dùng."""


def run_cremad6(waveform: np.ndarray) -> Dict[str, Any]:
    """{'name', 'probs' [6], 'labels' [6 tên nhãn], 'latency_ms', 'accuracy', 'macro_f1'} cho waveform 48.000 mẫu đã tiền xử lý; CrossModelNotReady nếu không chạy được."""
    from ml import inference

    try:
        entry = model_service.comparison_model(FAMILY)
    except model_service.RegistryUnavailable:
        raise CrossModelNotReady(MSG_REGISTRY_DOWN)
    if entry is None:
        raise CrossModelNotReady(MSG_NOT_REGISTERED)
    checkpoint = entry.get("checkpoint_path") or ""
    if not checkpoint or not Path(checkpoint).exists():
        raise CrossModelNotReady(MSG_MISSING_FILE.format(name=entry["name"], path=checkpoint or "—"))
    started = time.perf_counter()
    try:
        probs = inference.predict_aux(waveform, checkpoint, len(CREMAD6_NAMES))
    except Exception:
        logger.exception("Mô hình CREMA-D 6 nhãn lỗi")
        raise CrossModelNotReady(MSG_LOAD_FAILED)
    return {
        "name": entry["name"],
        "probs": probs,
        "labels": list(CREMAD6_NAMES),
        "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        "accuracy": entry["accuracy"],
        "macro_f1": entry["macro_f1"],
    }
