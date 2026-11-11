# Lịch sử phân tích và danh sách mẫu âm thanh có lọc/tìm kiếm.
# Mọi hàm chỉ trả dữ liệu của CHÍNH người dùng đang đăng nhập (kể cả Admin: mẫu của mọi người dùng xem ở trang Quản lý dữ liệu âm thanh).
# Phiên không có bản ghi nào (user_id <= 0) luôn trả rỗng. Trả dữ liệu thô (giây, xác suất 0–1, datetime); định dạng hiển thị là việc của giao diện.
import csv
import io
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select

from core.session import SessionUser, require_login
from db.session import get_session
from ml.config import EMOTION_NAMES
from models.audio_file import AudioFile
from models.emotion import Emotion
from models.ml_model import MLModel
from models.prediction import Prediction
from models.prediction_score import PredictionScore
from models.system_log import SystemLog
from services import audit_service
from services.audio_cleanup import drop_audio, remove_files

PAGE_SIZE_MAX = 100
MSG_BAD_DATE = "Ngày không hợp lệ, hãy chọn ngày trên lịch (năm-tháng-ngày)."
MSG_BAD_RANGE = "Ngày bắt đầu phải trước hoặc bằng ngày kết thúc."
MSG_FUTURE_DATE = "Không chọn được ngày chưa tới."
MSG_RECORD_NOT_FOUND = "Không tìm thấy bản ghi này (có thể đã bị xóa)."
CSV_HEADER = ["Tệp âm thanh", "Thời lượng (giây)", "Cảm xúc dự đoán", "Độ tin cậy (%)", "Mô hình", "Thời gian (UTC)"]


def _owner_id(session: SessionUser) -> Optional[int]:
    user = require_login(session)
    return None if user.is_demo else user.user_id


def _local_day(text: str) -> date:
    try:
        return date.fromisoformat(str(text).strip()[:10])
    except ValueError:
        raise ValueError(MSG_BAD_DATE)


def _day_start_utc(day: date) -> datetime:
    """0 giờ của ngày đó theo giờ máy chủ, đổi sang UTC (cùng cách tính với trang Nhật ký hệ thống)."""
    return datetime.combine(day, time.min, tzinfo=datetime.now().astimezone().tzinfo).astimezone(timezone.utc)


def _conditions(owner: int, emotion: Optional[str], days: Optional[int], q: Optional[str], date_from: Optional[str] = None, date_to: Optional[str] = None) -> list:
    conditions = [AudioFile.user_id == owner]
    if emotion:
        conditions.append(Emotion.name == emotion)
    if days:
        conditions.append(Prediction.created_at >= datetime.now(timezone.utc) - timedelta(days=days))
    first = _local_day(date_from) if date_from else None
    last = _local_day(date_to) if date_to else None
    today = datetime.now().astimezone().date()
    if (first and first > today) or (last and last > today):
        raise ValueError(MSG_FUTURE_DATE)
    if first and last and first > last:
        raise ValueError(MSG_BAD_RANGE)
    if first:
        conditions.append(Prediction.created_at >= _day_start_utc(first))
    if last:
        conditions.append(Prediction.created_at < _day_start_utc(last + timedelta(days=1)))
    text = (q or "").strip()
    if text:
        escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        conditions.append(AudioFile.filename.ilike(f"%{escaped}%", escape="\\"))
    return conditions


def _joined(*columns):
    return (
        select(*columns)
        .select_from(Prediction)
        .join(AudioFile, Prediction.audio_id == AudioFile.audio_id)
        .join(Emotion, Prediction.emotion_id == Emotion.emotion_id)
        .join(MLModel, Prediction.model_id == MLModel.model_id)
    )


def _row(prediction: Prediction, audio: AudioFile, emotion: Emotion, model: MLModel) -> Dict[str, Any]:
    return {
        "id": prediction.prediction_id,
        "file": audio.filename,
        "duration": audio.duration,
        "emotion": emotion.name,
        "confidence": prediction.confidence,
        "model": model.name,
        "created_at": prediction.created_at,
    }


def _ordered(stmt):
    return stmt.order_by(Prediction.created_at.desc(), Prediction.prediction_id.desc())


def list_history(
    session: SessionUser, page: int = 1, page_size: int = 10, emotion: Optional[str] = None, days: Optional[int] = None, q: Optional[str] = None,
    date_from: Optional[str] = None, date_to: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """(các dòng của trang, tổng số dòng khớp bộ lọc), mới nhất trước. emotion là tên nhãn tiếng Anh (vd 'angry'); days = 7 / 30 / None (tất cả)."""
    owner = _owner_id(session)
    if owner is None:
        return [], 0
    page_size = max(1, min(int(page_size), PAGE_SIZE_MAX))
    page = max(1, int(page))
    where = _conditions(owner, emotion, days, q, date_from, date_to)
    with get_session() as db:
        total = db.scalar(_joined(func.count(Prediction.prediction_id)).where(*where)) or 0
        rows = db.execute(_ordered(_joined(Prediction, AudioFile, Emotion, MLModel).where(*where)).limit(page_size).offset((page - 1) * page_size)).all()
        return [_row(*r) for r in rows], total


def first_record_date(session: SessionUser) -> Optional[date]:
    """Ngày (giờ máy chủ) của lượt phân tích đầu tiên của chính người dùng; None nếu chưa có. Dùng để giới hạn lịch chọn ngày."""
    owner = _owner_id(session)
    if owner is None:
        return None
    with get_session() as db:
        first = db.scalar(_joined(func.min(Prediction.created_at)).where(AudioFile.user_id == owner))
    if first is None:
        return None
    return (first if first.tzinfo else first.replace(tzinfo=timezone.utc)).astimezone().date()


def summarize_history(
    session: SessionUser, emotion: Optional[str] = None, days: Optional[int] = None, q: Optional[str] = None, date_from: Optional[str] = None, date_to: Optional[str] = None
) -> Dict[str, Any]:
    """{'total', 'avg_confidence' (0–1, 0 nếu rỗng)} trên TOÀN BỘ kết quả khớp bộ lọc, không chỉ trang hiện tại."""
    owner = _owner_id(session)
    if owner is None:
        return {"total": 0, "avg_confidence": 0.0}
    with get_session() as db:
        count, avg = db.execute(_joined(func.count(Prediction.prediction_id), func.avg(Prediction.confidence)).where(*_conditions(owner, emotion, days, q, date_from, date_to))).one()
        return {"total": count or 0, "avg_confidence": float(avg or 0.0)}


def get_history_detail(session: SessionUser, prediction_id: int) -> Optional[Dict[str, Any]]:
    """Chi tiết một lượt: như list_history + 'probs' (8 xác suất theo thứ tự nhãn), 'heatmap_path', 'mel_path', 'audio_path'. None nếu không có hoặc không thuộc user."""
    owner = _owner_id(session)
    if owner is None:
        return None
    with get_session() as db:
        found = db.execute(_joined(Prediction, AudioFile, Emotion, MLModel).where(Prediction.prediction_id == prediction_id, AudioFile.user_id == owner)).first()
        if found is None:
            return None
        prediction, audio, _, _ = found
        scores = {s.emotion_id: s.probability for s in db.scalars(select(PredictionScore).where(PredictionScore.prediction_id == prediction_id))}
        return {
            **_row(*found),
            "probs": [float(scores.get(i, 0.0)) for i in range(len(EMOTION_NAMES))],
            "heatmap_path": prediction.heatmap_path,
            "audio_path": audio.file_path,
            "mel_path": audio.features.mel_image_path if audio.features is not None else None,
        }


def list_audio_samples(session: SessionUser, q: Optional[str] = None, emotion: Optional[str] = None) -> List[Dict[str, Any]]:
    """Mẫu âm thanh của user (mới nhất trước), kèm kết quả phân tích gần nhất của từng mẫu (emotion/confidence là None nếu chưa phân tích)."""
    owner = _owner_id(session)
    if owner is None:
        return []
    with get_session() as db:
        latest = select(func.max(Prediction.prediction_id).label("pid")).group_by(Prediction.audio_id).subquery()
        stmt = (
            select(AudioFile, Prediction, Emotion)
            .outerjoin(Prediction, Prediction.audio_id == AudioFile.audio_id)
            .outerjoin(Emotion, Prediction.emotion_id == Emotion.emotion_id)
            .where(AudioFile.user_id == owner)
            .where((Prediction.prediction_id.is_(None)) | (Prediction.prediction_id.in_(select(latest.c.pid))))
        )
        text = (q or "").strip()
        if text:
            escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            stmt = stmt.where(AudioFile.filename.ilike(f"%{escaped}%", escape="\\"))
        if emotion:
            stmt = stmt.where(Emotion.name == emotion)
        stmt = stmt.order_by(AudioFile.uploaded_at.desc(), AudioFile.audio_id.desc())
        return [
            {
                "audio_id": audio.audio_id,
                "file": audio.filename,
                "duration": audio.duration,
                "uploaded_at": audio.uploaded_at,
                "file_path": audio.file_path,
                "emotion": emo.name if emo else None,
                "confidence": prediction.confidence if prediction else None,
            }
            for audio, prediction, emo in db.execute(stmt).all()
        ]


def _csv_safe(value: str) -> str:
    """Tên tệp do người dùng đặt: nếu bắt đầu bằng = + - @ thì Excel có thể chạy như công thức, nên thêm dấu nháy đơn phía trước."""
    return f"'{value}" if value[:1] in ("=", "+", "-", "@", "\t", "\r") else value


def export_history_csv(
    session: SessionUser, emotion: Optional[str] = None, days: Optional[int] = None, q: Optional[str] = None, date_from: Optional[str] = None, date_to: Optional[str] = None
) -> str:
    """Toàn bộ lịch sử khớp bộ lọc dạng CSV UTF-8 có BOM (Excel mở đúng tiếng Việt)."""
    owner = _owner_id(session)
    out = io.StringIO()
    out.write("﻿")
    writer = csv.writer(out)
    writer.writerow(CSV_HEADER)
    if owner is not None:
        with get_session() as db:
            for prediction, audio, emo, model in db.execute(_ordered(_joined(Prediction, AudioFile, Emotion, MLModel).where(*_conditions(owner, emotion, days, q, date_from, date_to)))).all():
                created = prediction.created_at if prediction.created_at.tzinfo else prediction.created_at.replace(tzinfo=timezone.utc)
                writer.writerow(
                    [_csv_safe(audio.filename), f"{audio.duration:.2f}", emo.name, f"{prediction.confidence * 100:.1f}", model.name, created.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")]
                )
    return out.getvalue()


# ---------- người dùng tự xóa dữ liệu của mình ----------
def _log_deletion(db, user: SessionUser, message: str) -> None:
    db.add(SystemLog(level="INFO", service="audio", message=audit_service.clean(message), user_id=user.user_id))  # cùng giao dịch với việc xóa; không ghi nội dung âm thanh


def count_audio(session: SessionUser) -> int:
    """Số mẫu âm thanh trong lịch sử của chính người dùng (0 với phiên không có tài khoản)."""
    owner = _owner_id(session)
    if owner is None:
        return 0
    with get_session() as db:
        return int(db.scalar(select(func.count(AudioFile.audio_id)).where(AudioFile.user_id == owner)) or 0)


def delete_history_item(session: SessionUser, prediction_id: int) -> Dict[str, Any]:
    """Xóa vĩnh viễn bản ghi lịch sử của CHÍNH người dùng: mẫu âm thanh của lượt đó cùng mọi lượt phân tích, điểm số, đặc trưng, tệp âm thanh,
    ảnh XAI và ảnh Mel. Bản ghi của người khác hoặc không có thì ValueError. Trả {'file', 'predictions', 'files_removed'}."""
    user = require_login(session)
    owner = _owner_id(session)
    if owner is None:
        raise ValueError(MSG_RECORD_NOT_FOUND)
    with get_session() as db:
        prediction = db.get(Prediction, prediction_id)
        audio = db.get(AudioFile, prediction.audio_id) if prediction is not None else None
        if audio is None or audio.user_id != owner:
            raise ValueError(MSG_RECORD_NOT_FOUND)
        summary = {"file": audio.filename, "predictions": len(audio.predictions)}
        paths = drop_audio(db, audio)
        _log_deletion(db, user, f"{user.username} xóa bản ghi '{summary['file']}' khỏi lịch sử của mình ({summary['predictions']} lượt phân tích)")
        db.commit()
    summary["files_removed"] = remove_files(paths)
    return summary


def delete_all_history(session: SessionUser) -> Dict[str, Any]:
    """Xóa vĩnh viễn toàn bộ lịch sử của CHÍNH người dùng (mọi mẫu âm thanh và dữ liệu đi kèm). Trả {'audio_files', 'predictions', 'files_removed'}."""
    user = require_login(session)
    owner = _owner_id(session)
    if owner is None:
        return {"audio_files": 0, "predictions": 0, "files_removed": 0}
    with get_session() as db:
        audios = list(db.scalars(select(AudioFile).where(AudioFile.user_id == owner)))
        predictions = sum(len(a.predictions) for a in audios)
        paths = [path for audio in audios for path in drop_audio(db, audio)]
        if audios:
            _log_deletion(db, user, f"{user.username} xóa toàn bộ lịch sử của mình ({len(audios)} mẫu âm thanh, {predictions} lượt phân tích)")
        db.commit()
    return {"audio_files": len(audios), "predictions": predictions, "files_removed": remove_files(paths)}
