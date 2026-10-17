# Tài khoản cá nhân (ngoài báo cáo, bổ sung cho UC01): xem và sửa họ tên, email, đổi mật khẩu của chính mình.
# Phiên "Vào thử" (user_id <= 0) không có dòng trong bảng users nên chỉ đổi trong phiên; tài khoản thật ghi vào DB.
# Đổi mật khẩu dùng core.security (bcrypt) nên chạy được khi UC01 cài xong hash_password / verify_password.
import re
from dataclasses import replace
from typing import Any, Dict

from sqlalchemy import func, select

from core.security import hash_password, verify_password
from core.session import SessionUser, require_login
from db.session import get_session
from models.system_log import SystemLog
from models.user import User

NAME_MAX = 100
EMAIL_MAX = 255
PASSWORD_MIN = 8
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MSG_NAME_EMPTY = "Vui lòng nhập họ và tên."
MSG_NAME_LONG = f"Họ và tên tối đa {NAME_MAX} ký tự."
MSG_EMAIL_INVALID = "Email không hợp lệ."
MSG_EMAIL_TAKEN = "Email này đã được dùng bởi tài khoản khác."
MSG_NOT_FOUND = "Không tìm thấy tài khoản hoặc tài khoản đã bị khóa."
MSG_PW_FILL = "Vui lòng nhập đầy đủ mật khẩu hiện tại và mật khẩu mới."
MSG_PW_MISMATCH = "Mật khẩu nhập lại không khớp."
MSG_PW_SHORT = f"Mật khẩu mới cần ít nhất {PASSWORD_MIN} ký tự."
MSG_PW_SAME = "Mật khẩu mới phải khác mật khẩu hiện tại."
MSG_PW_WRONG = "Mật khẩu hiện tại không đúng."
MSG_PW_DEMO = "Tài khoản thử nghiệm không có mật khẩu để đổi."


def _clean_name(full_name: str) -> str:
    name = " ".join((full_name or "").split())  # gộp khoảng trắng thừa, bỏ xuống dòng
    if not name:
        raise ValueError(MSG_NAME_EMPTY)
    if len(name) > NAME_MAX:
        raise ValueError(MSG_NAME_LONG)
    return name


def _clean_email(email: str) -> str:
    mail = (email or "").strip().lower()
    if len(mail) > EMAIL_MAX or not _EMAIL_RE.match(mail):
        raise ValueError(MSG_EMAIL_INVALID)
    return mail


def get_profile(session: SessionUser) -> Dict[str, Any]:
    """Thông tin hiển thị trên trang Tài khoản. created_at là chuỗi dd/mm/yyyy, None với phiên thử nghiệm."""
    user = require_login(session)
    if user.is_demo:
        return {"username": user.username, "email": user.email, "full_name": user.display_name, "role": user.role, "created_at": None, "demo": True}
    with get_session() as db:
        row = db.get(User, user.user_id)
        if row is None or not row.is_active:
            raise ValueError(MSG_NOT_FOUND)
        created = row.created_at.strftime("%d/%m/%Y") if row.created_at else None
        return {"username": row.username, "email": row.email, "full_name": row.full_name or "", "role": row.role, "created_at": created, "demo": False}


def update_profile(session: SessionUser, full_name: str, email: str) -> SessionUser:
    """Lưu họ tên và email của chính người dùng; trả SessionUser mới để giao diện cập nhật gr.State."""
    user = require_login(session)
    name, mail = _clean_name(full_name), _clean_email(email)
    if not user.is_demo:
        with get_session() as db:
            row = db.get(User, user.user_id)
            if row is None or not row.is_active:
                raise ValueError(MSG_NOT_FOUND)
            taken = db.scalar(select(User.user_id).where(func.lower(User.email) == mail, User.user_id != row.user_id))
            if taken is not None:
                raise ValueError(MSG_EMAIL_TAKEN)
            changed = [label for label, differs in (("họ tên", (row.full_name or "") != name), ("email", row.email != mail)) if differs]
            row.full_name, row.email = name, mail
            if changed:  # chỉ ghi TÊN trường đã đổi, không ghi giá trị mới hay cũ
                db.add(SystemLog(level="INFO", service="account", message=f"{row.username} cập nhật hồ sơ ({', '.join(changed)})", user_id=row.user_id))
            db.commit()
    return replace(user, display_name=name, email=mail)


def change_password(session: SessionUser, current_password: str, new_password: str, confirm_password: str) -> None:
    user = require_login(session)
    if not current_password or not new_password or not confirm_password:
        raise ValueError(MSG_PW_FILL)
    if new_password != confirm_password:
        raise ValueError(MSG_PW_MISMATCH)
    if len(new_password) < PASSWORD_MIN:
        raise ValueError(MSG_PW_SHORT)
    if new_password == current_password:
        raise ValueError(MSG_PW_SAME)
    if user.is_demo:
        raise ValueError(MSG_PW_DEMO)
    with get_session() as db:
        row = db.get(User, user.user_id)
        if row is None or not row.is_active:
            raise ValueError(MSG_NOT_FOUND)
        if not verify_password(current_password, row.password):
            db.add(SystemLog(level="WARNING", service="account", message=f"{row.username} nhập sai mật khẩu hiện tại khi đổi mật khẩu", user_id=row.user_id))
            db.commit()  # lưu dấu vết trước khi báo lỗi
            raise ValueError(MSG_PW_WRONG)
        row.password = hash_password(new_password)
        db.add(SystemLog(level="INFO", service="account", message=f"{row.username} đổi mật khẩu", user_id=row.user_id))
        db.commit()
