# UC01: băm mật khẩu (bcrypt) và mã đặt lại mật khẩu (yêu cầu phi chức năng: mật khẩu phải băm, báo cáo Mục 2.1.2).
# TODO: token đặt lại chỉ lưu dạng băm SHA-256 trong password_resets.token_hash.
import bcrypt

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


def generate_reset_token() -> str:
    raise NotImplementedError("TODO UC01 quên mật khẩu (đề cương tuần 9): sinh mã ngẫu nhiên bằng secrets.token_urlsafe, hiển thị cho người dùng một lần")


def hash_reset_token(token: str) -> str:
    raise NotImplementedError("TODO UC01 quên mật khẩu: SHA-256 của mã, lưu vào password_resets.token_hash")
