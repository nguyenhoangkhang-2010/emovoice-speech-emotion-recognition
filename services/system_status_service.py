# UC06: trạng thái dịch vụ (ứng dụng, mô hình, cơ sở dữ liệu, kho tệp) cho hàng trạng thái ở admin Tổng quan.
# Mỗi kiểm tra tự bắt lỗi của chính nó: một dịch vụ hỏng chỉ làm dòng của nó đỏ, không làm cả trang trạng thái lỗi.
# Khung Stitch ghi API Gateway/NGINX, GPU T4 — không có trong kiến trúc Gradio, nên thay bằng 4 dịch vụ thật của ứng dụng này.
import shutil
import sys
import time
import uuid
from typing import Any, Dict, List

from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError

from core.config import settings
from core.session import SessionUser, require_admin
from db.session import engine, get_session
from ml.config import EMOTION_NAMES
from models.emotion import Emotion
from services import admin_service, model_service

OK, WARN, BAD = "ok", "warn", "bad"
_ORDER = {OK: 0, WARN: 1, BAD: 2}
_STARTED = time.monotonic()  # mốc tính thời gian ứng dụng đã chạy (module được nạp lúc khởi động ứng dụng)
LOW_DISK_BYTES = 1 * 1024**3  # còn dưới 1 GiB thì cảnh báo
DB_LABELS = {"postgresql": "PostgreSQL", "sqlite": "SQLite", "mysql": "MySQL"}


def _service(key: str, name: str, description: str, state: str, metric: str) -> Dict[str, Any]:
    return {"key": key, "name": name, "description": description, "state": state, "metric": metric}


def _uptime_text(seconds: float) -> str:
    minutes = int(seconds // 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    if days:
        return f"{days} ngày {hours} giờ"
    if hours:
        return f"{hours} giờ {minutes} phút"
    return f"{minutes} phút" if minutes else "dưới 1 phút"


def _check_app() -> Dict[str, Any]:
    return _service("app", "Ứng dụng Gradio", "Giao diện web và xử lý yêu cầu", OK, f"Đã chạy {_uptime_text(time.monotonic() - _STARTED)}")


def _check_database() -> Dict[str, Any]:
    label = DB_LABELS.get(engine.dialect.name, engine.dialect.name)
    description = f"{label} (SQLAlchemy)"
    started = time.perf_counter()
    try:
        with get_session() as db:
            db.execute(text("SELECT 1"))
            latency_ms = (time.perf_counter() - started) * 1000
            seeded = db.scalar(select(func.count(Emotion.emotion_id))) or 0
    except Exception as exc:  # không kết nối được, sai mật khẩu, chưa chạy migration...
        return _service("database", "Cơ sở dữ liệu", description, BAD, f"Lỗi kết nối ({type(exc).__name__})")
    if seeded != len(EMOTION_NAMES):  # kết nối được nhưng thiếu 8 nhãn: thường do chưa chạy `python -m db.seed`
        return _service("database", "Cơ sở dữ liệu", description, WARN, f"Thiếu dữ liệu ban đầu ({seeded}/{len(EMOTION_NAMES)} nhãn)")
    return _service("database", "Cơ sở dữ liệu", description, OK, "<1 ms" if latency_ms < 1 else f"{latency_ms:.0f} ms")


def _check_storage() -> Dict[str, Any]:
    description = "Thư mục lưu âm thanh, ảnh XAI, nhật ký"
    folders = [settings.upload_dir, settings.heatmap_dir, settings.mel_dir, settings.log_dir]
    try:
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)
            probe = folder / f".write-test-{uuid.uuid4().hex}"
            probe.write_bytes(b"ok")  # ghi thử rồi xóa: kiểm tra quyền ghi thật, không chỉ kiểm tra thư mục tồn tại
            probe.unlink()
        free = shutil.disk_usage(settings.upload_dir).free
    except OSError as exc:
        return _service("storage", "Kho tệp", description, BAD, f"Không ghi được ({type(exc).__name__})")
    metric = f"Còn trống {free / 1024**3:.1f} GB"
    return _service("storage", "Kho tệp", description, WARN if free < LOW_DISK_BYTES else OK, metric)


def _model_loaded(path: str) -> bool:
    """Mô hình đã nằm trong bộ nhớ chưa. Không import ml.inference chỉ để hỏi (nạp PyTorch mất vài giây): chưa import nghĩa là chưa nạp."""
    module = sys.modules.get("ml.inference")
    if module is None:
        return False
    info = module.loaded_info()
    return bool(info["loaded"]) and info["path"] == path


def _check_model() -> Dict[str, Any]:
    name = "Mô hình AI"
    try:
        active = model_service.active_model()
    except model_service.RegistryUnavailable:
        return _service("model", name, "Chưa đọc được danh sách mô hình", BAD, "Cần cơ sở dữ liệu")
    if active is None:
        if settings.checkpoint_path.exists():
            return _service("model", name, "Dùng checkpoint dự phòng (MODEL_CHECKPOINT_PATH)", WARN, "Chưa đăng ký vào bảng models")
        return _service("model", name, "Chưa có mô hình đang dùng", BAD, "Cần chạy ml.register_model")
    description = f"{active['name']} đang dùng"
    path = active.get("checkpoint_path") or ""
    if not path or not _file_exists(path):
        return _service("model", name, description, BAD, "Thiếu tệp checkpoint")
    from services import inference_service

    last = inference_service.last_latency_ms()
    if _model_loaded(path):
        return _service("model", name, description, OK, f"Gần nhất {last:.0f} ms/mẫu" if last else "Đã nạp, chưa có lượt suy luận")
    return _service("model", name, description, OK, "Sẽ nạp ở lượt phân tích đầu tiên")


def _file_exists(path: str) -> bool:
    from pathlib import Path

    return Path(path).exists()


def get_system_status(session: SessionUser) -> Dict[str, Any]:
    """{'overall': 'ok'|'warn'|'bad', 'services': [{'key','name','description','state','metric'}, ...]}; chỉ admin.
    Quyền admin được đối chiếu lại CSDL như mọi chức năng quản trị; riêng trang này, khi chính CSDL hỏng thì quay về dùng vai trò trong phiên
    để vẫn báo được "Cơ sở dữ liệu: lỗi" thay vì tự sập đúng lúc admin cần xem sự cố."""
    try:
        admin_service.require_active_admin(session)
    except SQLAlchemyError:
        require_admin(session)
    services: List[Dict[str, Any]] = [_check_app(), _check_model(), _check_database(), _check_storage()]
    overall = max((s["state"] for s in services), key=lambda state: _ORDER[state])
    return {"overall": overall, "services": services}
