# Trang Mô hình & hiệu năng + admin Tổng quan: số liệu mô hình ĐỌC từ assets/metrics/*.json (xuất bởi ml/evaluate.py, ml/benchmark.py).
# load_metrics/load_confusion_matrix đã cài đặt (chỉ đọc tệp); phần đọc bảng models trong DB chưa cài đặt.
import json
from typing import Dict, List, Optional

from core.config import settings


def load_metrics() -> Dict[str, object]:
    path = settings.metrics_dir / "model_metrics.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_confusion_matrix(model_key: str) -> Optional[Dict[str, object]]:
    filenames = {"distilhubert_lora": "confusion_matrix_transformer.json", "random_forest": "confusion_matrix_random_forest.json"}
    name = filenames.get(model_key)
    if name is None:
        return None
    path = settings.metrics_dir / name
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def confusion_matrix_options() -> List[str]:
    return ["distilhubert_lora", "random_forest"]


def list_models_from_db():
    raise NotImplementedError("TODO: đọc bảng models (db) để đồng bộ với file metrics; hiện giao diện chỉ đọc file JSON")


def set_active_model(session, model_id: int) -> None:
    raise NotImplementedError("TODO admin_models: đặt is_active (chỉ 1 dòng true), gọi require_admin, ghi system_logs, nạp lại mô hình")
