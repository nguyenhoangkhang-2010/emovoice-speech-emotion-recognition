# UC01 quên mật khẩu (đề cương tuần 9; bảng password_resets chưa có trong báo cáo Mục 2.4) + gửi email (mail_service). Không gửi mạng thật.
import smtplib
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401  (đăng ký bảng vào Base.metadata)
from core.config import settings as real_settings
from core.security import generate_reset_token, hash_reset_token, tokens_match
from db.base import Base
from models.password_reset import PasswordReset
from models.system_log import SystemLog
from models.user import User
from services import auth_service as svc
from services import mail_service

SMTP = replace(real_settings, smtp_host="smtp.test", smtp_port=587, smtp_user="u@test", smtp_password="pw", smtp_from="EmoVoice <u@test>", reset_code_on_screen=False)
DEMO = replace(real_settings, smtp_host="", reset_code_on_screen=True)
NONE = replace(real_settings, smtp_host="", reset_code_on_screen=False)


@pytest.fixture()
def db(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False)

    @contextmanager
    def fake_get_session():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    monkeypatch.setattr(svc, "get_session", fake_get_session)
    svc._failures.clear()
    svc._reset_failures.clear()
    monkeypatch.setattr(svc, "settings", SMTP)
    monkeypatch.setattr(mail_service, "settings", SMTP)
    svc.register("anh", "an@example.com", "matkhau-cu-123", "matkhau-cu-123")
    return fake_get_session


@pytest.fixture()
def outbox(monkeypatch):
    sent = []
    monkeypatch.setattr(svc.mail_service, "send_reset_code", lambda to, code, ttl: sent.append((to, code, ttl)))
    return sent


def _backdate_resets(db, seconds):
    with db() as s:
        for row in s.query(PasswordReset):
            row.created_at = datetime.now(timezone.utc) - timedelta(seconds=seconds)
        s.commit()


def test_token_is_random_and_matches_only_its_own_hash():
    a, b = generate_reset_token(), generate_reset_token()
    assert a != b and a.isdigit() and len(a) == 6 and b.isdigit() and len(b) == 6  # đúng 6 chữ số
    assert tokens_match(a, hash_reset_token(a)) and tokens_match(f" {a} ", hash_reset_token(a)) and not tokens_match(b, hash_reset_token(a))
    assert len(hash_reset_token(a)) == 64 and a not in hash_reset_token(a)
    assert tokens_match(f"{a[:3]} {a[3:]}", hash_reset_token(a))  # gõ cách giữa hai nhóm ba số vẫn đúng


def test_reset_token_is_hashed_and_expires(db, outbox):
    assert svc.request_password_reset("An@Example.com") is None  # không trả mã ra giao diện khi gửi email thật
    to, code, ttl = outbox[0]
    assert to == "an@example.com" and ttl == real_settings.password_reset_ttl_minutes
    with db() as s:
        row = s.query(PasswordReset).one()
        assert row.token_hash == hash_reset_token(code) and code not in row.token_hash  # chỉ lưu bản băm
        expires = row.expires_at if row.expires_at.tzinfo else row.expires_at.replace(tzinfo=timezone.utc)
        assert timedelta(minutes=ttl - 1) < expires - datetime.now(timezone.utc) <= timedelta(minutes=ttl)
        assert row.used_at is None


def test_reset_token_is_single_use(db, outbox):
    svc.request_password_reset("an@example.com")
    code = outbox[0][1]
    svc.reset_password("an@example.com", code, "matkhau-moi-456")
    with pytest.raises(ValueError, match="không hợp lệ"):
        svc.reset_password("an@example.com", code, "matkhau-khac-789")
    assert svc.login("anh", "matkhau-moi-456").username == "anh"
    with pytest.raises(ValueError):
        svc.login("anh", "matkhau-cu-123")
    with db() as s:
        assert s.query(PasswordReset).one().used_at is not None
        assert any("Đặt lại mật khẩu" in r.message for r in s.query(SystemLog))


def test_expired_wrong_and_unknown_cases_share_one_message(db, outbox):
    svc.request_password_reset("an@example.com")
    code = outbox[0][1]
    with db() as s:
        s.query(PasswordReset).one().expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        s.commit()
    messages = set()
    for email, token in (("an@example.com", code), ("an@example.com", "ma-sai"), ("nguoi-la@x.vn", code), ("an@example.com", ""), ("khong-phai-email", code)):
        with pytest.raises(ValueError) as exc:
            svc.reset_password(email, token, "matkhau-moi-456")
        messages.add(str(exc.value))
    assert messages == {svc.MSG_RESET_INVALID}
    assert svc.login("anh", "matkhau-cu-123").username == "anh"  # mật khẩu cũ không đổi


def test_short_password_is_rejected_without_burning_the_code(db, outbox):
    svc.request_password_reset("an@example.com")
    code = outbox[0][1]
    with pytest.raises(ValueError, match="ít nhất 8"):
        svc.reset_password("an@example.com", code, "ngan")
    svc.reset_password("an@example.com", code, "matkhau-moi-456")  # mã vẫn dùng được sau lần nhập sai


def test_unknown_email_looks_identical_and_sends_nothing(db, outbox):
    for email in ("nguoi-la@x.vn", "", "khong-phai-email"):
        assert svc.request_password_reset(email) is None
    assert outbox == []
    with db() as s:
        assert s.query(PasswordReset).count() == 0


def test_locked_account_gets_no_code(db, outbox):
    with db() as s:
        s.query(User).one().is_active = False
        s.commit()
    assert svc.request_password_reset("an@example.com") is None and outbox == []


def test_repeated_requests_are_throttled_then_new_code_replaces_old(db, outbox):
    svc.request_password_reset("an@example.com")
    svc.request_password_reset("an@example.com")  # bấm liên tục trong 60 giây
    assert len(outbox) == 1
    _backdate_resets(db, 120)
    svc.request_password_reset("an@example.com")
    assert len(outbox) == 2
    first, second = outbox[0][1], outbox[1][1]
    with pytest.raises(ValueError):
        svc.reset_password("an@example.com", first, "matkhau-moi-456")  # mã cũ hết tác dụng khi có mã mới
    svc.reset_password("an@example.com", second, "matkhau-moi-456")


def test_without_smtp_or_demo_flag_it_refuses_instead_of_pretending(db, monkeypatch):
    monkeypatch.setattr(svc, "settings", NONE)
    with pytest.raises(mail_service.MailNotConfigured):
        svc.request_password_reset("an@example.com")
    with pytest.raises(mail_service.MailNotConfigured):
        svc.request_password_reset("nguoi-la@x.vn")  # lỗi cấu hình giống nhau, không lộ email nào tồn tại
    with db() as s:
        assert s.query(PasswordReset).count() == 0


def test_demo_flag_returns_code_for_known_email_only(db, monkeypatch):
    monkeypatch.setattr(svc, "settings", DEMO)
    assert svc.request_password_reset("nguoi-la@x.vn") is None
    code = svc.request_password_reset("an@example.com")
    assert code and code.isdigit() and len(code) == 6
    svc.reset_password("an@example.com", code, "matkhau-moi-456")


def test_mail_failure_is_logged_and_hidden_from_the_user(db, monkeypatch):
    def boom(to, code, ttl):
        raise mail_service.MailError("Gửi email thất bại: SMTPAuthenticationError")

    monkeypatch.setattr(svc.mail_service, "send_reset_code", boom)
    assert svc.request_password_reset("an@example.com") is None  # không báo lỗi để không lộ email có tồn tại
    with db() as s:
        assert any(r.level == "ERROR" and "SMTPAuthenticationError" in r.message for r in s.query(SystemLog))


# ---------- mail_service ----------
def test_reset_message_contains_code_and_lifetime(monkeypatch):
    monkeypatch.setattr(mail_service, "settings", SMTP)
    message = mail_service.build_reset_message("an@example.com", "ABC123xyz789", 15)
    body = message.get_body(preferencelist=("plain",)).get_content()  # bản văn bản thuần dự phòng
    assert message["To"] == "an@example.com" and message["From"] == "EmoVoice <u@test>" and "ABC123xyz789" in body and "15 phút" in body


def test_reset_message_has_styled_html_alternative(monkeypatch):
    monkeypatch.setattr(mail_service, "settings", SMTP)
    message = mail_service.build_reset_message("an@example.com", "048213", 15)
    assert message.is_multipart() and message.get_body(preferencelist=("html",)) is not None
    html = message.get_body(preferencelist=("html",)).get_content()
    assert "048213" in html and "15 phút" in html and "#F2EFE7" in html and "#14130F" in html and "gradient" not in html  # màu giấy/mực của web, không gradient


def test_html_email_escapes_its_inputs():
    html = mail_service.build_reset_html("<script>x</script>", 15)
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_send_requires_smtp_host(monkeypatch):
    monkeypatch.setattr(mail_service, "settings", NONE)
    with pytest.raises(mail_service.MailNotConfigured):
        mail_service.send_reset_code("an@example.com", "x", 15)


class _FakeSMTP:
    instances = []

    def __init__(self, host, port, timeout=None):
        self.calls = [("connect", host, port)]
        _FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self, context=None):
        self.calls.append(("starttls",))

    def login(self, user, password):
        self.calls.append(("login", user))

    def send_message(self, message):
        self.calls.append(("send", message["To"]))


def test_send_uses_starttls_login_then_sends(monkeypatch):
    _FakeSMTP.instances.clear()
    monkeypatch.setattr(mail_service, "settings", SMTP)
    monkeypatch.setattr(mail_service.smtplib, "SMTP", _FakeSMTP)
    mail_service.send_reset_code("an@example.com", "code", 15)
    assert _FakeSMTP.instances[0].calls == [("connect", "smtp.test", 587), ("starttls",), ("login", "u@test"), ("send", "an@example.com")]


def test_send_wraps_network_errors(monkeypatch):
    def refuse(*args, **kwargs):
        raise smtplib.SMTPConnectError(421, "no")

    monkeypatch.setattr(mail_service, "settings", SMTP)
    monkeypatch.setattr(mail_service.smtplib, "SMTP", refuse)
    with pytest.raises(mail_service.MailError):
        mail_service.send_reset_code("an@example.com", "code", 15)


# ---------- mã 6 số ----------
def test_code_keeps_leading_zeros(monkeypatch):
    monkeypatch.setattr("core.security.secrets.randbelow", lambda n: 42)
    assert generate_reset_token() == "000042"


def test_hash_depends_on_secret_key(monkeypatch):
    # băm có khóa bí mật: lộ bảng password_resets cũng không đảo ngược được 10^6 mã chỉ bằng SHA-256 thường
    import hashlib

    assert hash_reset_token("123456") != hashlib.sha256(b"123456").hexdigest()
    before = hash_reset_token("123456")
    monkeypatch.setattr("core.security.settings", replace(real_settings, secret_key="khoa-khac"))
    assert hash_reset_token("123456") != before


def test_wrong_codes_are_limited_then_code_is_destroyed(db, outbox):
    svc.request_password_reset("an@example.com")
    code = outbox[0][1]
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(svc.MAX_RESET_ATTEMPTS):
        with pytest.raises(ValueError, match="không hợp lệ"):
            svc.reset_password("an@example.com", wrong, "matkhau-moi-456")
    with pytest.raises(ValueError, match="quá nhiều lần"):
        svc.reset_password("an@example.com", code, "matkhau-moi-456")  # đã bị chặn: mã đúng cũng không dùng được nữa
    with db() as s:
        assert s.query(PasswordReset).one().used_at is not None  # mã bị hủy trong DB
        assert any("nhập sai quá nhiều lần" in r.message for r in s.query(SystemLog))
    with pytest.raises(ValueError):
        svc.login("anh", "matkhau-moi-456")


def test_destroyed_code_stays_dead_even_if_counter_is_lost(db, outbox):
    svc.request_password_reset("an@example.com")
    code = outbox[0][1]
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(svc.MAX_RESET_ATTEMPTS):
        with pytest.raises(ValueError):
            svc.reset_password("an@example.com", wrong, "matkhau-moi-456")
    svc._reset_failures.clear()  # giả lập khởi động lại tiến trình
    with pytest.raises(ValueError, match="không hợp lệ"):
        svc.reset_password("an@example.com", code, "matkhau-moi-456")


def test_new_code_gives_a_fresh_attempt_budget(db, outbox):
    svc.request_password_reset("an@example.com")
    for _ in range(svc.MAX_RESET_ATTEMPTS):
        with pytest.raises(ValueError):
            svc.reset_password("an@example.com", "not-the-code", "matkhau-moi-456")
    _backdate_resets(db, 120)
    svc.request_password_reset("an@example.com")
    svc.reset_password("an@example.com", outbox[1][1], "matkhau-moi-456")


def test_unknown_email_is_throttled_the_same_way(db):
    for _ in range(svc.MAX_RESET_ATTEMPTS):
        with pytest.raises(ValueError, match="không hợp lệ"):
            svc.reset_password("nguoi-la@x.vn", "123456", "matkhau-moi-456")
    with pytest.raises(ValueError, match="quá nhiều lần"):
        svc.reset_password("nguoi-la@x.vn", "123456", "matkhau-moi-456")  # không lộ email nào có tài khoản


# ---------- xác nhận mã trước khi cho đặt mật khẩu mới ----------
def test_verify_accepts_correct_code_without_consuming_it(db, outbox):
    svc.request_password_reset("an@example.com")
    code = outbox[0][1]
    svc.verify_reset_code("an@example.com", code)
    svc.verify_reset_code("An@Example.com", f"{code[:3]} {code[3:]}")  # kiểm tra lại vẫn được, gõ cách vẫn được
    with db() as s:
        assert s.query(PasswordReset).one().used_at is None
    with pytest.raises(ValueError):
        svc.login("anh", "matkhau-moi-456")  # chỉ xác nhận mã thì chưa đổi mật khẩu
    svc.reset_password("an@example.com", code, "matkhau-moi-456")  # bước 3 vẫn dùng được mã đó


def test_verify_rejects_wrong_expired_used_and_unknown_with_one_message(db, outbox):
    svc.request_password_reset("an@example.com")
    code = outbox[0][1]
    wrong = "000000" if code != "000000" else "111111"
    for email, token in (("an@example.com", wrong), ("an@example.com", ""), ("nguoi-la@x.vn", code), ("khong-phai-email", code)):
        with pytest.raises(ValueError) as exc:
            svc.verify_reset_code(email, token)
        assert str(exc.value) == svc.MSG_RESET_INVALID
    svc.reset_password("an@example.com", code, "matkhau-moi-456")
    with pytest.raises(ValueError, match="không hợp lệ"):
        svc.verify_reset_code("an@example.com", code)  # mã đã dùng xong thì không xác nhận lại được


def test_verify_counts_toward_the_same_attempt_limit(db, outbox):
    svc.request_password_reset("an@example.com")
    code = outbox[0][1]
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(svc.MAX_RESET_ATTEMPTS):
        with pytest.raises(ValueError, match="không hợp lệ"):
            svc.verify_reset_code("an@example.com", wrong)
    with pytest.raises(ValueError, match="quá nhiều lần"):
        svc.verify_reset_code("an@example.com", code)
    with pytest.raises(ValueError, match="quá nhiều lần"):
        svc.reset_password("an@example.com", code, "matkhau-moi-456")  # đoán mò bằng bước 2 cũng không vòng qua được giới hạn


def test_verify_rejects_expired_code(db, outbox):
    svc.request_password_reset("an@example.com")
    code = outbox[0][1]
    with db() as s:
        s.query(PasswordReset).one().expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        s.commit()
    with pytest.raises(ValueError, match="không hợp lệ"):
        svc.verify_reset_code("an@example.com", code)
