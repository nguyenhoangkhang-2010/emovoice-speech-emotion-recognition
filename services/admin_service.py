# UC06 (báo cáo Bảng 2.8): thống kê, quản lý tài khoản, nhật ký, dữ liệu âm thanh. MỌI hàm nhận session và gọi require_admin ở dòng đầu.
# Thống kê, người dùng (khóa, vai trò, mật khẩu tạm), nhật ký và dữ liệu âm thanh (xem, xóa). Trả dữ liệu thô (số, datetime); định dạng hiển thị là việc của giao diện.
import secrets
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, or_, select, update

from sqlalchemy.exc import IntegrityError

from core.config import settings
from core.security import hash_password
from core.session import PermissionDenied, SessionUser, require_admin
from db.session import get_session
from ml.config import EMOTION_NAMES
from models.audio_file import AudioFile
from models.emotion import Emotion
from models.password_reset import PasswordReset
from models.prediction import Prediction
from models.system_log import SystemLog
from models.user import ROLE_ADMIN, ROLE_USER, User
from services import auth_service

PAGE_SIZE_MAX = 100
WEEKDAYS = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]  # date.weekday(): thứ Hai = 0
LOG_LEVELS = ("INFO", "WARNING", "ERROR")
LOG_SERVICES = ("auth", "account", "admin", "audio", "preprocess", "inference", "xai", "baseline", "model")  # dịch vụ ghi nhật ký, dùng cho ô lọc

MSG_USER_NOT_FOUND = "Không tìm thấy tài khoản này."
MSG_SELF_LOCK = "Bạn không thể tự khóa chính tài khoản đang đăng nhập."
MSG_BAD_DATE = "Ngày không hợp lệ, hãy nhập dạng năm-tháng-ngày (ví dụ 2026-10-17)."
MSG_BAD_LEVEL = "Mức nhật ký không hợp lệ."
MSG_BAD_SERVICE = "Dịch vụ không hợp lệ."
MSG_BAD_ROLE = "Vai trò không hợp lệ."
MSG_NAME_LONG = "Họ và tên tối đa 100 ký tự."
MSG_AUDIO_NOT_FOUND = "Không tìm thấy mẫu âm thanh này (có thể đã bị xóa)."
MSG_SELF_DEMOTE = "Bạn không thể tự thu hồi quyền quản trị của chính mình."
MSG_PROMOTE_LOCKED = "Không thể cấp quyền quản trị cho tài khoản đang bị khóa. Hãy mở khóa trước."
MSG_LAST_ADMIN = "Phải còn ít nhất một quản trị viên đang hoạt động."


def _page(page: int, page_size: int) -> Tuple[int, int]:
    return max(1, int(page)), max(1, min(int(page_size), PAGE_SIZE_MAX))


def _like(column, text: str):
    # ILIKE: PostgreSQL không phân biệt hoa/thường cả chữ có dấu; SQLite (chỉ để phát triển) chỉ làm được với chữ ASCII.
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")  # % và _ người dùng gõ là ký tự thường
    return column.ilike(f"%{escaped}%", escape="\\")


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)  # SQLite trả datetime không múi giờ (UTC)


def _log(db, level: str, message: str, user_id: Optional[int]) -> None:
    db.add(SystemLog(level=level, service="admin", message=message, user_id=user_id if user_id and user_id > 0 else None))


def _admin(session: Optional[SessionUser]) -> SessionUser:
    """Chỉ admin được gọi. Ngoài vai trò ghi trong phiên còn đối chiếu lại CSDL: admin bị khóa hoặc bị thu quyền thì phiên đang mở
    cũng mất quyền ngay, không phải chờ họ đăng xuất. Phiên "Vào thử" (user_id <= 0) không có dòng trong users nên không kiểm tra thêm."""
    admin = require_admin(session)
    if not admin.is_demo:
        with get_session() as db:
            row = db.get(User, admin.user_id)
            if row is None or not row.is_active or row.role != ROLE_ADMIN:
                raise PermissionDenied("Chức năng này chỉ dành cho Quản trị viên.")
    return admin


require_active_admin = _admin  # tên công khai cho các dịch vụ khác (system_status_service)


# ---------- thống kê (trang Tổng quan) ----------
def get_stats(session: SessionUser) -> Dict[str, Any]:
    """{'analyses', 'analyses_week', 'analyses_prev_week', 'accounts', 'accounts_total', 'accounts_locked',
    'daily_labels' / 'daily_values' (7 ngày gần nhất theo giờ máy chủ, cũ -> mới), 'distribution' {nhãn: số lượt}}."""
    _admin(session)
    now = datetime.now(timezone.utc)
    today = datetime.now().astimezone().date()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    local_tz = datetime.now().astimezone().tzinfo
    start = datetime.combine(days[0], time.min, tzinfo=local_tz)
    with get_session() as db:
        analyses = db.scalar(select(func.count(Prediction.prediction_id))) or 0
        week = db.scalar(select(func.count(Prediction.prediction_id)).where(Prediction.created_at >= now - timedelta(days=7))) or 0
        prev_week = db.scalar(select(func.count(Prediction.prediction_id)).where(Prediction.created_at >= now - timedelta(days=14), Prediction.created_at < now - timedelta(days=7))) or 0
        accounts_total = db.scalar(select(func.count(User.user_id))) or 0
        accounts = db.scalar(select(func.count(User.user_id)).where(User.is_active.is_(True))) or 0
        per_day = {d: 0 for d in days}
        for (created,) in db.execute(select(Prediction.created_at).where(Prediction.created_at >= start)):
            day = _aware(created).astimezone(local_tz).date()
            if day in per_day:
                per_day[day] += 1
        counts = dict(db.execute(select(Emotion.name, func.count(Prediction.prediction_id)).select_from(Emotion).outerjoin(Prediction, Prediction.emotion_id == Emotion.emotion_id).group_by(Emotion.name)).all())
    return {
        "analyses": analyses,
        "analyses_week": week,
        "analyses_prev_week": prev_week,
        "accounts": accounts,
        "accounts_total": accounts_total,
        "accounts_locked": accounts_total - accounts,
        "daily_labels": [WEEKDAYS[d.weekday()] for d in days],
        "daily_values": [per_day[d] for d in days],
        "distribution": {name: int(counts.get(name, 0)) for name in EMOTION_NAMES},
    }


# ---------- tài khoản ----------
def list_users(session: SessionUser, page: int = 1, page_size: int = 10, q: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
    """(các dòng của trang, tổng) theo thứ tự tạo tài khoản. 'usage' là số lượt phân tích của tài khoản."""
    _admin(session)
    page, page_size = _page(page, page_size)
    text = (q or "").strip()
    where = [or_(_like(User.username, text), _like(User.email, text), _like(User.full_name, text))] if text else []
    with get_session() as db:
        total = db.scalar(select(func.count(User.user_id)).where(*where)) or 0
        usage = (
            select(AudioFile.user_id.label("uid"), func.count(Prediction.prediction_id).label("n"))
            .join(Prediction, Prediction.audio_id == AudioFile.audio_id)
            .group_by(AudioFile.user_id)
            .subquery()
        )
        rows = db.execute(
            select(User, func.coalesce(usage.c.n, 0))
            .outerjoin(usage, usage.c.uid == User.user_id)
            .where(*where)
            .order_by(User.user_id)
            .limit(page_size)
            .offset((page - 1) * page_size)
        ).all()
        return [
            {
                "user_id": u.user_id,
                "username": u.username,
                "full_name": u.full_name or "",
                "email": u.email,
                "role": u.role,
                "usage": int(n),
                "active": bool(u.is_active),
                "created_at": u.created_at,
            }
            for u, n in rows
        ], total


def set_user_status(session: SessionUser, user_id: int, is_active: bool) -> None:
    """Khóa / mở khóa tài khoản và ghi system_logs. Admin không tự khóa chính mình (tránh mất quyền quản trị).
    Tài khoản bị khóa không đăng nhập được nữa; phiên đã mở sẵn vẫn còn cho tới khi người đó đăng xuất."""
    admin = _admin(session)
    if not is_active and user_id == admin.user_id:
        raise ValueError(MSG_SELF_LOCK)
    with get_session() as db:
        target = db.get(User, user_id)
        if target is None:
            raise ValueError(MSG_USER_NOT_FOUND)
        target.is_active = bool(is_active)
        _log(db, "INFO", f"{admin.username} {'mở khóa' if is_active else 'khóa'} tài khoản {target.username}", admin.user_id)
        db.commit()


def set_user_role(session: SessionUser, user_id: int, role: str) -> bool:
    """Cấp quyền quản trị (role='Admin') hoặc thu hồi (role='User'). Trả True nếu có thay đổi, False nếu tài khoản đã đúng vai trò đó.
    Ràng buộc: admin không tự thu quyền chính mình; không cấp quyền cho tài khoản đang bị khóa; luôn còn ít nhất một admin đang hoạt động.
    Ghi system_logs mức WARNING vì đây là thay đổi quyền."""
    admin = _admin(session)
    if role not in (ROLE_USER, ROLE_ADMIN):
        raise ValueError(MSG_BAD_ROLE)
    if role == ROLE_USER and user_id == admin.user_id:
        raise ValueError(MSG_SELF_DEMOTE)
    with get_session() as db:
        target = db.get(User, user_id)
        if target is None:
            raise ValueError(MSG_USER_NOT_FOUND)
        if target.role == role:
            return False
        if role == ROLE_ADMIN and not target.is_active:
            raise ValueError(MSG_PROMOTE_LOCKED)
        if role == ROLE_USER:
            others = db.scalar(select(func.count(User.user_id)).where(User.role == ROLE_ADMIN, User.is_active.is_(True), User.user_id != user_id)) or 0
            if others == 0:
                raise ValueError(MSG_LAST_ADMIN)
        target.role = role
        _log(db, "WARNING", f"{admin.username} {'cấp quyền quản trị cho' if role == ROLE_ADMIN else 'thu hồi quyền quản trị của'} tài khoản {target.username}", admin.user_id)
        db.commit()
        return True


def create_user(session: SessionUser, username: str, email: str, role: str = ROLE_USER, full_name: str = "") -> Dict[str, Any]:
    """Admin tạo tài khoản cho người khác. Hệ thống sinh MẬT KHẨU TẠM (admin không phải đặt hay biết mật khẩu của người dùng), trả về MỘT lần
    để chuyển cho người đó; chỉ lưu bản băm bcrypt. Kiểm tra giống lúc tự đăng ký. Cấp vai trò Admin được ghi nhật ký mức WARNING."""
    admin = _admin(session)
    username = (username or "").strip()
    email = (email or "").strip().lower()
    name = " ".join((full_name or "").split())
    if not auth_service.USERNAME_RE.match(username):
        raise ValueError(auth_service.MSG_USERNAME_INVALID)
    if len(email) > auth_service.EMAIL_MAX or not auth_service.EMAIL_RE.match(email):
        raise ValueError(auth_service.MSG_EMAIL_INVALID)
    if len(name) > 100:
        raise ValueError(MSG_NAME_LONG)
    if role not in (ROLE_USER, ROLE_ADMIN):
        raise ValueError(MSG_BAD_ROLE)
    temp = secrets.token_urlsafe(9)
    hashed = hash_password(temp)
    with get_session() as db:
        if db.scalar(select(User.user_id).where(or_(func.lower(User.username) == username.lower(), func.lower(User.email) == email))) is not None:
            raise ValueError(auth_service.MSG_TAKEN)
        user = User(username=username, email=email, full_name=name or None, password=hashed, role=role)
        db.add(user)
        try:
            db.flush()
        except IntegrityError:  # hai admin tạo cùng lúc
            db.rollback()
            raise ValueError(auth_service.MSG_TAKEN)
        _log(db, "WARNING" if role == ROLE_ADMIN else "INFO", f"{admin.username} tạo tài khoản {username} (vai trò {role})", admin.user_id)
        db.commit()
        return {"user_id": user.user_id, "username": username, "email": email, "role": role, "temp_password": temp}


def reset_user_password(session: SessionUser, user_id: int) -> str:
    """Cấp mật khẩu tạm cho người dùng quên mật khẩu mà không có email (đường dự phòng). Trả mật khẩu tạm MỘT lần để admin
    chuyển cho người đó; mật khẩu cũ và các mã đặt lại đang chờ mất tác dụng. Người dùng nên đổi lại ở trang Tài khoản của tôi."""
    admin = _admin(session)
    temp = secrets.token_urlsafe(9)
    with get_session() as db:
        target = db.get(User, user_id)
        if target is None:
            raise ValueError(MSG_USER_NOT_FOUND)
        target.password = hash_password(temp)
        db.execute(update(PasswordReset).where(PasswordReset.user_id == user_id, PasswordReset.used_at.is_(None)).values(used_at=datetime.now(timezone.utc)))
        _log(db, "WARNING", f"{admin.username} cấp mật khẩu tạm cho tài khoản {target.username}", admin.user_id)
        db.commit()
    return temp


# ---------- nhật ký ----------
def _day_range(on_date: str) -> Tuple[datetime, datetime]:
    """Một ngày theo giờ máy chủ -> [bắt đầu, kết thúc) tính theo UTC."""
    try:
        day = date.fromisoformat(on_date.strip())
    except ValueError:
        raise ValueError(MSG_BAD_DATE)
    local_tz = datetime.now().astimezone().tzinfo
    begin = datetime.combine(day, time.min, tzinfo=local_tz)
    return begin.astimezone(timezone.utc), (begin + timedelta(days=1)).astimezone(timezone.utc)


def list_logs(
    session: SessionUser, page: int = 1, page_size: int = 10, level: Optional[str] = None, on_date: Optional[str] = None, q: Optional[str] = None,
    service: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """(các dòng của trang, tổng) mới nhất trước. level: INFO | WARNING | ERROR; on_date: 'YYYY-MM-DD' theo giờ máy chủ; q: tìm trong nội dung và tên dịch vụ; service: một trong LOG_SERVICES."""
    _admin(session)
    page, page_size = _page(page, page_size)
    where = []
    if level:
        if level not in LOG_LEVELS:
            raise ValueError(MSG_BAD_LEVEL)
        where.append(SystemLog.level == level)
    if service:
        if service not in LOG_SERVICES:
            raise ValueError(MSG_BAD_SERVICE)
        where.append(SystemLog.service == service)
    if on_date and on_date.strip():
        begin, end = _day_range(on_date)
        where.append(SystemLog.created_at >= begin)
        where.append(SystemLog.created_at < end)
    text = (q or "").strip()
    if text:
        where.append(or_(_like(SystemLog.message, text), _like(SystemLog.service, text)))
    with get_session() as db:
        total = db.scalar(select(func.count(SystemLog.log_id)).where(*where)) or 0
        rows = db.execute(
            select(SystemLog, User.username)
            .outerjoin(User, SystemLog.user_id == User.user_id)
            .where(*where)
            .order_by(SystemLog.created_at.desc(), SystemLog.log_id.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        ).all()
        return [{"id": log.log_id, "level": log.level, "service": log.service, "message": log.message, "user": username, "created_at": log.created_at} for log, username in rows], total


# ---------- dữ liệu âm thanh (trang Quản lý dữ liệu âm thanh) ----------
def list_all_audio(
    session: SessionUser, page: int = 1, page_size: int = 10, q: Optional[str] = None, emotion: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], int]:
    """Mẫu âm thanh của MỌI người dùng (mới nhất trước) kèm kết quả phân tích gần nhất. q: tên tệp hoặc tên tài khoản; emotion: nhãn của
    kết quả gần nhất (vd 'angry'). 'predictions' là số lượt phân tích của mẫu, 'emotion'/'confidence' là None nếu chưa phân tích."""
    _admin(session)
    page, page_size = _page(page, page_size)
    latest = select(func.max(Prediction.prediction_id).label("pid")).group_by(Prediction.audio_id).subquery()
    counts = select(Prediction.audio_id.label("aid"), func.count(Prediction.prediction_id).label("n")).group_by(Prediction.audio_id).subquery()
    where = []
    text = (q or "").strip()
    if text:
        where.append(or_(_like(AudioFile.filename, text), _like(User.username, text)))
    if emotion:
        where.append(Emotion.name == emotion)
    base = (
        select(AudioFile, User.username, Prediction, Emotion, func.coalesce(counts.c.n, 0))
        .join(User, AudioFile.user_id == User.user_id)
        .outerjoin(Prediction, (Prediction.audio_id == AudioFile.audio_id) & Prediction.prediction_id.in_(select(latest.c.pid)))
        .outerjoin(Emotion, Prediction.emotion_id == Emotion.emotion_id)
        .outerjoin(counts, counts.c.aid == AudioFile.audio_id)
        .where(*where)
    )
    with get_session() as db:
        total = db.scalar(select(func.count()).select_from(base.with_only_columns(AudioFile.audio_id).subquery())) or 0
        rows = db.execute(base.order_by(AudioFile.uploaded_at.desc(), AudioFile.audio_id.desc()).limit(page_size).offset((page - 1) * page_size)).all()
        return [
            {
                "audio_id": audio.audio_id,
                "file": audio.filename,
                "duration": audio.duration,
                "user": username,
                "owner_id": audio.user_id,
                "uploaded_at": audio.uploaded_at,
                "file_path": audio.file_path,
                "emotion": emo.name if emo else None,
                "confidence": pred.confidence if pred else None,
                "predictions": int(n),
            }
            for audio, username, pred, emo, n in rows
        ], total


def _remove_stored_file(path: Optional[str], allowed_dirs: List[Path]) -> bool:
    """Xóa một tệp CHỈ khi nó nằm trong thư mục lưu trữ của ứng dụng (đường dẫn trong CSDL không được tin tuyệt đối). Trả True nếu đã xóa."""
    if not path:
        return False
    try:
        target = Path(path).resolve()
        if not any(base.resolve() in target.parents for base in allowed_dirs):
            return False
        target.unlink()
        return True
    except OSError:  # tệp đã mất hoặc đang bị khóa: bỏ qua, dòng trong CSDL vẫn được xóa
        return False


def delete_audio(session: SessionUser, audio_id: int) -> Dict[str, Any]:
    """Xóa vĩnh viễn một mẫu: các lượt phân tích (kèm 8 điểm số), đặc trưng, dòng audio_files, tệp âm thanh, ảnh XAI và ảnh Mel.
    CSDL được xóa trước (một giao dịch); tệp chỉ xóa sau khi giao dịch thành công. Trả tóm tắt {'file', 'user', 'predictions', 'files_removed'}. Ghi system_logs."""
    admin = _admin(session)
    with get_session() as db:
        audio = db.get(AudioFile, audio_id)
        if audio is None:
            raise ValueError(MSG_AUDIO_NOT_FOUND)
        owner = db.get(User, audio.user_id)
        predictions = list(audio.predictions)
        paths = [audio.file_path, *(p.heatmap_path for p in predictions)]
        if audio.features is not None:
            paths.append(audio.features.mel_image_path)
        summary = {"file": audio.filename, "user": owner.username if owner else "?", "predictions": len(predictions)}
        for prediction in predictions:
            db.delete(prediction)  # kéo theo prediction_scores (cascade)
        db.delete(audio)  # kéo theo audio_features (cascade)
        _log(db, "WARNING", f"{admin.username} xóa mẫu âm thanh '{summary['file']}' của {summary['user']} ({summary['predictions']} lượt phân tích)", admin.user_id)
        db.commit()
    allowed = [settings.upload_dir, settings.heatmap_dir, settings.mel_dir]
    summary["files_removed"] = sum(_remove_stored_file(p, allowed) for p in paths)
    return summary
