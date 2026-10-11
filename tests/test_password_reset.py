# UC01 quên mật khẩu (đề cương tuần 9; bảng password_resets chưa có trong báo cáo Mục 2.4).
import pytest


@pytest.mark.skip(reason="TODO UC01: request_password_reset lưu token_hash (không lưu mã thô), hết hạn sau PASSWORD_RESET_TTL_MINUTES")
def test_reset_token_is_hashed_and_expires():
    ...


@pytest.mark.skip(reason="TODO UC01: reset_password dùng mã một lần (used_at), từ chối mã hết hạn hoặc đã dùng")
def test_reset_token_is_single_use():
    ...
