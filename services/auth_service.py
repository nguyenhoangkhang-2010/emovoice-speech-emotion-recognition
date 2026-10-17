# UC01 (báo cáo Bảng 2.3): đăng ký, đăng nhập, đăng xuất, quên mật khẩu (đề cương tuần 9). Trả SessionUser cho gr.State.
# Nguyên tắc: mật khẩu chỉ lưu dạng bcrypt; sai tên hay sai mật khẩu cùng một thông báo; quên mật khẩu không lộ email nào đã đăng ký.
import re
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import IntegrityError

from core.config import settings
from core.security import generate_reset_token, hash_password, hash_reset_token, tokens_match, verify_password
from core.session import SessionUser
from db.session import get_session
from models.password_reset import PasswordReset
from models.system_log import SystemLog
from models.user import ROLE_USER, User
from services import mail_service

USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]{3,50}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
EMAIL_MAX = 255
PASSWORD_MIN = 8
MAX_FAILED_LOGINS = 5
LOGIN_WINDOW_SECONDS = 600
RESET_COOLDOWN_SECONDS = 60
MAX_RESET_ATTEMPTS = 5  # mã chỉ có 6 số: nhập sai quá số lần này thì mã bị hủy, phải xin mã mới

MSG_USERNAME_INVALID = "Tên đăng nhập 3–50 ký tự, chỉ gồm chữ cái, số, dấu chấm, gạch dưới hoặc gạch ngang."
MSG_EMAIL_INVALID = "Email không hợp lệ."
MSG_PASSWORD_SHORT = f"Mật khẩu cần ít nhất {PASSWORD_MIN} ký tự."
MSG_PASSWORD_MISMATCH = "Mật khẩu nhập lại không khớp."
MSG_TAKEN = "Tên đăng nhập hoặc email đã được sử dụng."
MSG_LOGIN_ERROR = "Sai tài khoản hoặc mật khẩu"
MSG_LOCKED = "Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên."
MSG_TOO_MANY = "Đăng nhập sai quá nhiều lần. Vui lòng thử lại sau vài phút."
MSG_RESET_INVALID = "Mã không hợp lệ hoặc đã hết hạn."
MSG_RESET_TOO_MANY = "Bạn đã nhập sai mã quá nhiều lần. Vui lòng yêu cầu mã mới."

# Đếm lần đăng nhập sai theo tên đăng nhập (trong bộ nhớ tiến trình, đủ để chặn dò mật khẩu cơ bản).
_failures: Dict[str, List[float]] = {}
_reset_failures: Dict[str, int] = {}  # số lần nhập sai mã đặt lại theo email
_failures_lock = threading.Lock()
_DUMMY_HASH = hash_password("khong-ai-biet-mat-khau-nay")  # so khớp giả khi không có tài khoản, để thời gian phản hồi không lộ tên nào tồn tại


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)  # SQLite trả datetime không múi giờ


def _log(db, level: str, message: str, user_id: Optional[int] = None) -> None:
    db.add(SystemLog(level=level, service="auth", message=message, user_id=user_id))


def _session_of(user: User) -> SessionUser:
    return SessionUser(user_id=user.user_id, username=user.username, email=user.email, role=user.role, display_name=user.full_name or "")


def _check_password_rules(password: str) -> None:
    if len(password or "") < PASSWORD_MIN:
        raise ValueError(MSG_PASSWORD_SHORT)


def _too_many_failures(key: str) -> bool:
    cutoff = time.monotonic() - LOGIN_WINDOW_SECONDS
    with _failures_lock:
        recent = [t for t in _failures.get(key, []) if t > cutoff]
        _failures[key] = recent
        return len(recent) >= MAX_FAILED_LOGINS


def _record_failure(key: str) -> None:
    with _failures_lock:
        _failures.setdefault(key, []).append(time.monotonic())


def _clear_failures(key: str) -> None:
    with _failures_lock:
        _failures.pop(key, None)


def register(username: str, email: str, password: str, confirm_password: str) -> SessionUser:
    username = (username or "").strip()
    email = (email or "").strip().lower()
    if not USERNAME_RE.match(username):
        raise ValueError(MSG_USERNAME_INVALID)
    if len(email) > EMAIL_MAX or not EMAIL_RE.match(email):
        raise ValueError(MSG_EMAIL_INVALID)
    _check_password_rules(password)
    if password != confirm_password:
        raise ValueError(MSG_PASSWORD_MISMATCH)
    hashed = hash_password(password)
    with get_session() as db:
        taken = db.scalar(select(User.user_id).where(or_(func.lower(User.username) == username.lower(), func.lower(User.email) == email)))
        if taken is not None:
            raise ValueError(MSG_TAKEN)
        user = User(username=username, email=email, password=hashed, role=ROLE_USER)
        db.add(user)
        try:
            db.flush()
        except IntegrityError:  # hai người đăng ký cùng lúc
            db.rollback()
            raise ValueError(MSG_TAKEN)
        _log(db, "INFO", f"Đăng ký tài khoản: {username}", user.user_id)
        db.commit()
        return _session_of(user)


def login(username_or_email: str, password: str) -> SessionUser:
    ident = (username_or_email or "").strip().lower()
    if not ident or not password:
        raise ValueError(MSG_LOGIN_ERROR)
    if _too_many_failures(ident):
        raise ValueError(MSG_TOO_MANY)
    with get_session() as db:
        user = db.scalar(select(User).where(or_(func.lower(User.username) == ident, func.lower(User.email) == ident)))
        valid = verify_password(password, user.password if user else _DUMMY_HASH)
        if user is None or not valid:
            _record_failure(ident)
            _log(db, "WARNING", f"Đăng nhập thất bại: {ident[:60]}", user.user_id if user else None)
            db.commit()
            raise ValueError(MSG_LOGIN_ERROR)
        if not user.is_active:  # chỉ nói "bị khóa" khi đã đúng mật khẩu, người lạ không dò được tài khoản nào bị khóa
            _log(db, "WARNING", f"Tài khoản bị khóa cố đăng nhập: {user.username}", user.user_id)
            db.commit()
            raise ValueError(MSG_LOCKED)
        _clear_failures(ident)
        _log(db, "INFO", f"Đăng nhập: {user.username}", user.user_id)
        db.commit()
        return _session_of(user)


def logout(session: SessionUser) -> None:
    if session is None or session.is_demo:
        return
    with get_session() as db:
        _log(db, "INFO", f"Đăng xuất: {session.username}", session.user_id)
        db.commit()


def request_password_reset(email: str) -> Optional[str]:
    """Tạo mã đặt lại và gửi qua email. Giao diện luôn hiện cùng một thông báo dù email có tồn tại hay không.

    Trả về mã CHỈ khi bật RESET_CODE_ON_SCREEN=1 (chế độ demo, KHÔNG an toàn vì ai biết email cũng nhận được mã); ngược lại trả None.
    MailNotConfigured nếu không có SMTP và cũng không bật chế độ demo (lỗi cấu hình, không lộ thông tin tài khoản)."""
    on_screen = settings.reset_code_on_screen
    if not settings.smtp_configured and not on_screen:
        raise mail_service.MailNotConfigured("Chưa cấu hình gửi email.")
    email = (email or "").strip().lower()
    with get_session() as db:
        user = db.scalar(select(User).where(func.lower(User.email) == email)) if EMAIL_RE.match(email) else None
        if user is None or not user.is_active:
            return None
        now = _now()
        latest = db.scalar(select(func.max(PasswordReset.created_at)).where(PasswordReset.user_id == user.user_id))
        if latest is not None and (now - _aware(latest)).total_seconds() < RESET_COOLDOWN_SECONDS:
            return None  # bấm liên tục: không tạo thêm mã, không gửi thêm thư
        db.execute(update(PasswordReset).where(PasswordReset.user_id == user.user_id, PasswordReset.used_at.is_(None)).values(used_at=now))  # mã cũ hết tác dụng
        _reset_failures.pop(email, None)  # mã mới được nhập sai tối đa MAX_RESET_ATTEMPTS lần
        code = generate_reset_token()
        ttl = settings.password_reset_ttl_minutes
        db.add(PasswordReset(user_id=user.user_id, token_hash=hash_reset_token(code), expires_at=now + timedelta(minutes=ttl)))
        _log(db, "INFO", f"Yêu cầu đặt lại mật khẩu: {user.username}", user.user_id)
        db.commit()
        if settings.smtp_configured:
            try:
                mail_service.send_reset_code(user.email, code, ttl)
            except mail_service.MailError as exc:
                _log(db, "ERROR", f"Không gửi được email đặt lại mật khẩu cho {user.username}: {exc}", user.user_id)
                db.commit()
        return code if on_screen else None


def _normalize_reset_input(email: str, token: str):
    return (email or "").strip().lower(), "".join((token or "").split())


def _check_reset_budget(email: str) -> None:
    with _failures_lock:
        if _reset_failures.get(email, 0) >= MAX_RESET_ATTEMPTS:
            raise ValueError(MSG_RESET_TOO_MANY)


def _find_valid_reset(db, email: str, token: str, now: datetime):
    """(user, bản ghi mã còn hiệu lực khớp với token hoặc None). Chỉ đọc, không đổi gì."""
    user = db.scalar(select(User).where(func.lower(User.email) == email)) if EMAIL_RE.match(email) else None
    if user is None or not user.is_active or not token:
        return user, None
    candidates = db.scalars(select(PasswordReset).where(PasswordReset.user_id == user.user_id, PasswordReset.used_at.is_(None)))
    return user, next((r for r in candidates if _aware(r.expires_at) > now and tokens_match(token, r.token_hash)), None)


def _reject_reset(db, email: str, user: Optional[User], now: datetime) -> None:
    """Ghi nhận một lần nhập sai; đủ MAX_RESET_ATTEMPTS lần thì hủy mã ngay trong DB. Luôn ném cùng một thông báo."""
    with _failures_lock:
        _reset_failures[email] = _reset_failures.get(email, 0) + 1
        exhausted = _reset_failures[email] >= MAX_RESET_ATTEMPTS
    if exhausted and user is not None:  # hủy cả khi bộ đếm trong bộ nhớ bị mất (khởi động lại)
        db.execute(update(PasswordReset).where(PasswordReset.user_id == user.user_id, PasswordReset.used_at.is_(None)).values(used_at=now))
        _log(db, "WARNING", f"Hủy mã đặt lại mật khẩu do nhập sai quá nhiều lần: {user.username}", user.user_id)
        db.commit()
    raise ValueError(MSG_RESET_INVALID)  # cùng một thông báo cho email lạ, mã sai, mã hết hạn hoặc đã dùng


def verify_reset_code(email: str, token: str) -> None:
    """Bước 2 của quên mật khẩu: kiểm tra mã đúng và còn hạn rồi mới cho nhập mật khẩu mới. KHÔNG tiêu thụ mã
    (reset_password vẫn kiểm tra lại mã khi đặt mật khẩu). Nhập sai tính vào cùng giới hạn MAX_RESET_ATTEMPTS."""
    email, token = _normalize_reset_input(email, token)
    _check_reset_budget(email)
    with get_session() as db:
        now = _now()
        user, matched = _find_valid_reset(db, email, token, now)
        if matched is None:
            _reject_reset(db, email, user, now)


def reset_password(email: str, token: str, new_password: str) -> None:
    _check_password_rules(new_password)
    email, token = _normalize_reset_input(email, token)
    _check_reset_budget(email)
    with get_session() as db:
        now = _now()
        user, matched = _find_valid_reset(db, email, token, now)
        if matched is None:
            _reject_reset(db, email, user, now)
        user.password = hash_password(new_password)
        db.execute(update(PasswordReset).where(PasswordReset.user_id == user.user_id, PasswordReset.used_at.is_(None)).values(used_at=now))
        _log(db, "INFO", f"Đặt lại mật khẩu: {user.username}", user.user_id)
        db.commit()
    with _failures_lock:
        _reset_failures.pop(email, None)
