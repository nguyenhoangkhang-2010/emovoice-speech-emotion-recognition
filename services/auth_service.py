# UC01 (báo cáo Bảng 2.3): đăng ký, đăng nhập, đăng xuất, quên mật khẩu (đề cương tuần 9). Trả SessionUser cho gr.State.
# Chưa cài đặt: giao diện bắt NotImplementedError và hiện thông báo.
from core.session import SessionUser


def register(username: str, email: str, password: str, confirm_password: str) -> SessionUser:
    raise NotImplementedError("TODO UC01: kiểm tra trùng username/email, độ mạnh mật khẩu, băm bcrypt, tạo users (role=User)")


def login(username_or_email: str, password: str) -> SessionUser:
    raise NotImplementedError("TODO UC01: xác thực, từ chối is_active=False, ghi system_logs (đăng nhập thành công/thất bại)")


def logout(session: SessionUser) -> None:
    raise NotImplementedError("TODO UC01: ghi system_logs; giao diện xóa gr.State")


def request_password_reset(email: str) -> str:
    raise NotImplementedError(
        "TODO UC01 quên mật khẩu (đề cương tuần 9): sinh mã, lưu password_resets.token_hash + expires_at (PASSWORD_RESET_TTL_MINUTES); "
        "chưa có SMTP nên bản demo hiển thị mã trên giao diện; luôn trả cùng thông báo dù email có tồn tại hay không"
    )


def reset_password(email: str, token: str, new_password: str) -> None:
    raise NotImplementedError("TODO UC01 quên mật khẩu: kiểm tra mã chưa dùng/chưa hết hạn, băm mật khẩu mới, đặt used_at")
