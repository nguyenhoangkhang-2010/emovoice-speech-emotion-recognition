# Danh mục mô hình THẬT: mọi số liệu đọc từ bảng models (được ghi bởi `python -m ml.register_model`, không chép tay).
# load_metrics() giữ nguyên dạng dữ liệu cũ nên các trang Mô hình & hiệu năng, Quản lý mô hình, Tổng quan không phải đổi cách dùng.
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional, Tuple

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from core.session import SessionUser, require_admin
from db.session import get_session
from models.ml_model import MLModel
from models.system_log import SystemLog


class RegistryUnavailable(Exception):
    """Không đọc / ghi được bảng models (chưa chạy `alembic upgrade head`, hoặc DB không kết nối được)."""


@contextmanager
def _db() -> Iterator:
    try:
        with get_session() as db:
            yield db
    except SQLAlchemyError as exc:
        raise RegistryUnavailable("Không truy cập được bảng models. Hãy kiểm tra DATABASE_URL và chạy `python -m alembic upgrade head`.") from exc


def _key(row: MLModel) -> str:
    return str(row.model_id)


def _to_dict(row: MLModel) -> Dict[str, Any]:
    ratio = round(row.params_trainable / row.params_total * 100, 2) if row.params_total and row.params_trainable is not None else None
    latency = (row.details or {}).get("latency", {})
    note = f"Thiết bị {row.latency_device}, batch {latency.get('batch_size', 1)}, có khởi động trước" if row.latency_device else ""
    return {
        "key": _key(row),
        "name": row.name,
        "model_type": row.model_type,
        "accuracy": row.accuracy,
        "macro_f1": row.f1_score,
        "size_mib": row.size_mb,
        "latency_ms": row.inference_time,
        "status": "active" if row.is_active else "ready",
        "params_total": row.params_total,
        "params_trainable": row.params_trainable,
        "trainable_ratio_pct": ratio,
        "latency_device": row.latency_device,
        "latency_note": note,
        "eval_dataset": row.eval_dataset,
        "eval_samples": row.eval_samples,
        "checkpoint_path": row.checkpoint_path,
    }


def _ordered(db) -> List[MLModel]:
    rows = list(db.scalars(select(MLModel)))
    return sorted(rows, key=lambda r: (not r.is_active, -(r.accuracy or 0), r.name))


def load_metrics() -> Dict[str, Any]:
    """{'dataset', 'test_samples', 'active_model' (key hoặc None), 'models': [...]}; models rỗng nếu chưa đăng ký mô hình nào."""
    with _db() as db:
        rows = _ordered(db)
        models = [_to_dict(r) for r in rows]
        lead = next((r for r in rows if r.is_active), rows[0] if rows else None)
        return {
            "dataset": lead.eval_dataset if lead else "",
            "test_samples": lead.eval_samples if lead else 0,
            "active_model": _key(next(r for r in rows if r.is_active)) if any(r.is_active for r in rows) else None,
            "models": models,
        }


def active_model() -> Optional[Dict[str, Any]]:
    metrics = load_metrics()
    return next((m for m in metrics["models"] if m["key"] == metrics["active_model"]), None)


def load_confusion_matrix(model_key: str) -> Optional[Dict[str, Any]]:
    with _db() as db:
        row = db.get(MLModel, int(model_key)) if str(model_key).isdigit() else None
        confusion = (row.details or {}).get("confusion") if row else None
        if not confusion:
            return None
        return {**confusion, "model_key": _key(row), "model_name": row.name, "dataset": row.eval_dataset}


def confusion_matrix_options() -> List[Tuple[str, str]]:
    """[(tên mô hình, key)] của các mô hình đã có ma trận nhầm lẫn."""
    with _db() as db:
        return [(r.name, _key(r)) for r in _ordered(db) if (r.details or {}).get("confusion")]


def _log(db, user_id: Optional[int], message: str) -> None:
    db.add(SystemLog(level="INFO", service="model", message=message, user_id=user_id if user_id and user_id > 0 else None))


def _activate(db, row: MLModel) -> None:
    """Đặt đúng một mô hình đang dùng (ràng buộc duy nhất is_active): tắt các dòng khác, đẩy xuống DB, rồi bật dòng này."""
    db.execute(update(MLModel).where(MLModel.model_id != row.model_id, MLModel.is_active.is_(True)).values(is_active=False))
    db.flush()
    row.is_active = True


def register_model(
    *,
    name: str,
    model_type: str,
    checkpoint_path: str,
    accuracy: float,
    f1_score: float,
    size_mb: float,
    inference_time: float,
    params_total: int,
    params_trainable: int,
    eval_dataset: str,
    eval_samples: int,
    latency_device: str,
    details: Dict[str, Any],
    activate: bool = False,
) -> Dict[str, Any]:
    """Thêm mô hình, hoặc cập nhật nếu đã có mô hình cùng tên (đăng ký lại sau khi huấn luyện lại / đo lại)."""
    with _db() as db:
        row = db.scalar(select(MLModel).where(MLModel.name == name))
        created = row is None
        if row is None:
            row = MLModel(name=name, model_type=model_type)
            db.add(row)
        row.model_type = model_type
        row.checkpoint_path = checkpoint_path
        row.accuracy, row.f1_score, row.size_mb, row.inference_time = accuracy, f1_score, size_mb, inference_time
        row.params_total, row.params_trainable = params_total, params_trainable
        row.eval_dataset, row.eval_samples, row.latency_device = eval_dataset, eval_samples, latency_device
        row.evaluated_at = datetime.now(timezone.utc)
        row.details = details
        db.flush()
        if activate:
            _activate(db, row)
        _log(db, None, f"{'Đăng ký' if created else 'Đo lại'} mô hình {name}: accuracy {accuracy}%, F1 {f1_score}%")
        db.commit()
        return _to_dict(row)


def set_active_model(session: Optional[SessionUser], model_key: str) -> Dict[str, Any]:
    """Đặt mô hình đang dùng (chỉ 1 dòng true). Chỉ admin; ghi system_logs."""
    admin = require_admin(session)
    with _db() as db:
        row = db.get(MLModel, int(model_key)) if str(model_key).isdigit() else None
        if row is None:
            raise ValueError("Không tìm thấy mô hình này.")
        _activate(db, row)
        _log(db, admin.user_id, f"Đặt mô hình đang dùng: {row.name}")
        db.commit()
        return _to_dict(row)
