# UC01: băm mật khẩu (bcrypt) và mã đặt lại mật khẩu (yêu cầu phi chức năng: mật khẩu phải băm, báo cáo Mục 2.1.2).
# Mã đặt lại là 6 chữ số, chỉ lưu dạng băm HMAC-SHA256 (khóa SECRET_KEY) trong password_resets.token_hash; mã thô chỉ tồn tại trong email.
# Mã ngắn thì phải chặn đoán mò: auth_service giới hạn số lần nhập sai rồi hủy mã (băm SHA-256 thường của 10^6 mã đảo ngược được ngay, nên cần khóa bí mật).
import hashlib
import hmac
import secrets

import bcrypt

from core.config import settings

BCRYPT_MAX_BYTES = 72  # bcrypt chỉ dùng 72 byte đầu của mật khẩu; từ chối thay vì âm thầm cắt bớt


def hash_password(plain_password: str) -> str:
    raw = plain_password.encode("utf-8")
    if len(raw) > BCRYPT_MAX_BYTES:
        raise ValueError(f"Mật khẩu tối đa {BCRYPT_MAX_BYTES} byte.")
    return bcrypt.hashpw(raw, bcrypt.gensalt()).decode("ascii")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    raw = plain_password.encode("utf-8")
    if len(raw) > BCRYPT_MAX_BYTES:
        return False
    try:
        return bcrypt.checkpw(raw, hashed_password.encode("ascii"))
    except ValueError:  # hash hỏng / không phải bcrypt
        return False


RESET_CODE_DIGITS = 6


def generate_reset_token() -> str:
    """Mã 6 chữ số ngẫu nhiên (000000–999999) từ nguồn ngẫu nhiên của hệ điều hành, giữ cả số 0 đầu."""
    return f"{secrets.randbelow(10 ** RESET_CODE_DIGITS):0{RESET_CODE_DIGITS}d}"


def hash_reset_token(token: str) -> str:
    """HMAC-SHA256 của mã (bỏ khoảng trắng người dùng gõ thừa) với khóa SECRET_KEY."""
    normalized = "".join((token or "").split())
    return hmac.new(settings.secret_key.encode("utf-8"), normalized.encode("utf-8"), hashlib.sha256).hexdigest()


def tokens_match(token: str, token_hash: str) -> bool:
    """So khớp mã người dùng nhập với bản băm đã lưu, thời gian so sánh không phụ thuộc vị trí ký tự sai."""
    return hmac.compare_digest(hash_reset_token(token), token_hash)
