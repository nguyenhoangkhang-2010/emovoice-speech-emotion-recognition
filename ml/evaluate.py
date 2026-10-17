# Đánh giá mô hình: Accuracy, Precision, Recall, F1 (macro), confusion matrix chuẩn hóa theo hàng (đề cương tuần 8; báo cáo Mục 5.1).
# Số đo được tính trên tập kiểm thử thật rồi ghi vào bảng models (ml/registry.py); UI chỉ đọc bảng đó.
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Union

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support

from ml.config import EMOTION_NAMES, EMOTION_NAMES_VI, NUM_CLASSES, NUM_SAMPLES


def load_eval_set(path: Union[str, Path]) -> Tuple[np.ndarray, np.ndarray]:
    """Đọc X_test [N, 48000], y_test [N] từ tệp .npz (cache sóng âm của ser_project: Actor 22-24, độc lập người nói)."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Không thấy tập kiểm thử: {path}. Đặt EVAL_DATASET_PATH trong .env trỏ tới waveforms_cache.npz.")
    with np.load(path) as data:
        x, y = data["X_test"].astype(np.float32), data["y_test"].astype(np.int64)
    if x.ndim != 2 or x.shape[1] != NUM_SAMPLES or len(x) != len(y):
        raise ValueError(f"Tập kiểm thử sai dạng: X_test {x.shape}, y_test {y.shape} (cần [N, {NUM_SAMPLES}] và [N]).")
    return x, y


def load_eval_features(path: Union[str, Path]) -> Tuple[np.ndarray, np.ndarray]:
    """Đọc X_test [N, 212], y_test [N] từ features_212_cache.npz (cùng cách chia diễn viên với tập sóng âm)."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Không thấy tập đặc trưng kiểm thử: {path}. Đặt EVAL_FEATURES_PATH trong .env trỏ tới features_212_cache.npz.")
    with np.load(path) as data:
        x, y = data["X_test"].astype(np.float32), data["y_test"].astype(np.int64)
    if x.ndim != 2 or x.shape[1] != 212 or len(x) != len(y):
        raise ValueError(f"Tập đặc trưng sai dạng: X_test {x.shape}, y_test {y.shape} (cần [N, 212] và [N]).")
    return x, y


def predict_all(model, x: np.ndarray, device, batch_size: int = 16) -> np.ndarray:
    """Chạy mô hình PyTorch (logits, attn) trên toàn bộ x, trả nhãn dự đoán [N]."""
    import torch

    preds: List[np.ndarray] = []
    model.eval()
    with torch.no_grad():
        for i in range(0, len(x), batch_size):
            logits, _ = model(torch.from_numpy(x[i : i + batch_size]).to(device))
            preds.append(logits.argmax(dim=1).cpu().numpy())
    return np.concatenate(preds)


def compute_metrics(y_true: Sequence[int], y_pred: Sequence[int]) -> Dict[str, object]:
    """Accuracy + macro Precision/Recall/F1 + từng lớp, tất cả tính bằng % (làm tròn 2 chữ số)."""
    labels = list(range(NUM_CLASSES))
    precision, recall, f1, support = precision_recall_fscore_support(y_true, y_pred, labels=labels, zero_division=0)
    per_class = [
        {
            "label": EMOTION_NAMES[i],
            "label_vi": EMOTION_NAMES_VI[i],
            "support": int(support[i]),
            "precision": round(float(precision[i]) * 100, 2),
            "recall": round(float(recall[i]) * 100, 2),
            "f1": round(float(f1[i]) * 100, 2),
        }
        for i in labels
    ]
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)) * 100, 2),
        "macro_precision": round(float(np.mean(precision)) * 100, 2),
        "macro_recall": round(float(np.mean(recall)) * 100, 2),
        "macro_f1": round(float(np.mean(f1)) * 100, 2),
        "per_class": per_class,
    }


def confusion_matrix_counts(y_true: Sequence[int], y_pred: Sequence[int]) -> np.ndarray:
    return confusion_matrix(y_true, y_pred, labels=list(range(NUM_CLASSES)))


def confusion_matrix_normalized(y_true: Sequence[int], y_pred: Sequence[int]) -> np.ndarray:
    """Ma trận 8x8 chuẩn hóa theo hàng (mỗi hàng có mẫu thì tổng = 1); hàng không có mẫu giữ 0."""
    counts = confusion_matrix_counts(y_true, y_pred).astype(np.float64)
    totals = counts.sum(axis=1, keepdims=True)
    return np.divide(counts, totals, out=np.zeros_like(counts), where=totals > 0)


def summarize(y_true: Sequence[int], y_pred: Sequence[int]) -> Dict[str, object]:
    """Số đo + ma trận nhầm lẫn (đếm và chuẩn hóa), sẵn sàng ghi vào models.details."""
    result = compute_metrics(y_true, y_pred)
    result["confusion"] = {
        "labels": EMOTION_NAMES,
        "labels_vi": EMOTION_NAMES_VI,
        "support": [c["support"] for c in result["per_class"]],
        "matrix_counts": confusion_matrix_counts(y_true, y_pred).tolist(),
        "matrix_normalized": np.round(confusion_matrix_normalized(y_true, y_pred), 4).tolist(),
    }
    return result


def evaluate_model(model, x: np.ndarray, y: np.ndarray, device) -> Dict[str, object]:
    return summarize(y, predict_all(model, x, device))
