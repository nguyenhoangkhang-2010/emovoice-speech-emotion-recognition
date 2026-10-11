# UC01: băm mật khẩu (bcrypt) và mã đặt lại mật khẩu (yêu cầu phi chức năng: mật khẩu phải băm, báo cáo Mục 2.1.2).
# TODO: dùng thư viện bcrypt; token đặt lại chỉ lưu dạng băm SHA-256 trong password_resets.token_hash.
def hash_password(plain_password: str) -> str:
    raise NotImplementedError("TODO UC01: băm mật khẩu bằng bcrypt.hashpw (báo cáo Mục 2.1.2)")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    raise NotImplementedError("TODO UC01: so khớp mật khẩu với hash bằng bcrypt.checkpw")


def generate_reset_token() -> str:
    raise NotImplementedError("TODO UC01 quên mật khẩu (đề cương tuần 9): sinh mã ngẫu nhiên bằng secrets.token_urlsafe, hiển thị cho người dùng một lần")


def hash_reset_token(token: str) -> str:
    raise NotImplementedError("TODO UC01 quên mật khẩu: SHA-256 của mã, lưu vào password_resets.token_hash")
