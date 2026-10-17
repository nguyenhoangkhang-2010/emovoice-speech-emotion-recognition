# Baseline cổ điển Random Forest: nạp tệp .pkl (scikit-learn) đã đăng ký và dự đoán 8 xác suất từ 212 đặc trưng âm học.
# Chỉ nạp tệp do quản trị viên đăng ký bằng `python -m ml.register_baseline` (pickle có thể chạy mã khi nạp, đừng nạp tệp lạ).
from __future__ import annotations

import threading

import numpy as np

from ml.config import NUM_CLASSES

FEATURE_DIM = 212
_cache = {"path": None, "model": None}
_lock = threading.Lock()  # Gradio chạy nhiều yêu cầu song song: chỉ nạp một lần


def load_random_forest(path: str):
    with _lock:
        if _cache["path"] != path:
            import joblib

            model = joblib.load(path)
            if getattr(model, "n_features_in_", FEATURE_DIM) != FEATURE_DIM:
                raise ValueError(f"Mô hình nhận {model.n_features_in_} đặc trưng, cần {FEATURE_DIM}.")
            if hasattr(model, "n_jobs"):
                model.n_jobs = 1  # một mẫu mỗi lần: chạy song song theo cây chỉ thêm chi phí khởi tạo luồng
            _cache.update(path=path, model=model)
        return _cache["model"]


def predict_probs(features: np.ndarray, path: str) -> np.ndarray:
    """212 đặc trưng -> 8 xác suất theo thứ tự nhãn của hệ thống (nhãn mô hình chưa từng thấy có xác suất 0)."""
    model = load_random_forest(path)
    raw = model.predict_proba(np.asarray(features, dtype=np.float32).reshape(1, -1))[0]
    probs = np.zeros(NUM_CLASSES, dtype=np.float64)
    for label, value in zip(model.classes_, raw):
        probs[int(label)] = value
    return probs
