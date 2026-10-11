# Đánh giá mô hình: Accuracy, Precision, Recall, F1 (macro), confusion matrix chuẩn hóa theo hàng (đề cương tuần 8; báo cáo Mục 5.1).
# Ghi assets/metrics/model_metrics.json và confusion_matrix_<mô hình>.json — UI (trang Mô hình & hiệu năng, admin Tổng quan) chỉ đọc hai loại file này.
from __future__ import annotations

from typing import Dict, Sequence

import numpy as np


def compute_metrics(y_true: Sequence[int], y_pred: Sequence[int]) -> Dict[str, object]:
    raise NotImplementedError("TODO (báo cáo Mục 5.1): Accuracy + macro Precision/Recall/F1 + per-class bằng scikit-learn")


def confusion_matrix_normalized(y_true: Sequence[int], y_pred: Sequence[int]) -> np.ndarray:
    raise NotImplementedError("TODO (báo cáo Hình 4.1, 4.2): ma trận 8x8 chuẩn hóa theo hàng (mỗi hàng tổng = 1)")


def write_metrics_json(model_key: str, metrics: Dict[str, object], output_dir: str = "assets/metrics") -> str:
    raise NotImplementedError("TODO: cập nhật mục models[model_key] trong model_metrics.json, giữ nguyên các mô hình khác")


def write_confusion_matrix_json(model_key: str, matrix: np.ndarray, support: Sequence[int], output_dir: str = "assets/metrics") -> str:
    raise NotImplementedError("TODO: ghi confusion_matrix_<model_key>.json theo schema trong assets/metrics (labels, support, matrix_counts, matrix_normalized)")
