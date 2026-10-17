# Gửi email (hiện chỉ dùng cho mã đặt lại mật khẩu của UC01). SMTP cấu hình trong .env: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM.
# Để trống SMTP_HOST thì coi như chưa cấu hình: auth_service sẽ không hứa gửi mã và giao diện báo rõ cho người dùng.
import smtplib
import ssl
from email.message import EmailMessage
from html import escape

from core.config import settings


class MailNotConfigured(Exception):
    """Chưa đặt SMTP_HOST trong .env."""


class MailError(Exception):
    """Có cấu hình nhưng gửi thất bại (sai mật khẩu ứng dụng, mất mạng, bị chặn cổng...)."""


# Thư HTML cùng phong cách web: nền giấy, chữ mực, chữ serif cho tiêu đề, nhãn mono, góc vuông, chấm xanh chanh để nhấn, không gradient.
# Bảng + CSS nội tuyến vì ứng dụng email không hỗ trợ tệp CSS ngoài; font web không tải được nên dùng Georgia / Courier làm dự phòng.
PAPER, INK, LIME, RULE, MUTED, ALT = "#F2EFE7", "#14130F", "#D6F23E", "#CFC9B8", "#77736A", "#E8E4D8"
SERIF = "Newsreader, Georgia, 'Times New Roman', serif"
SANS = "'Be Vietnam Pro', 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "'IBM Plex Mono', 'Courier New', Courier, monospace"


def build_reset_html(code: str, ttl_minutes: int) -> str:
    code, ttl = escape(code), escape(str(ttl_minutes))
    label = f"font-family:{MONO};font-size:11px;letter-spacing:1.6px;text-transform:uppercase;color:{MUTED};"
    return f"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EmoVoice – Mã đặt lại mật khẩu</title></head>
<body style="margin:0;padding:0;background:{ALT};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{ALT};"><tr><td align="center" style="padding:32px 12px;">
  <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="width:100%;max-width:560px;background:{PAPER};border-top:4px solid {INK};">
    <tr><td style="padding:28px 32px 0 32px;">
      <table role="presentation" cellpadding="0" cellspacing="0"><tr>
        <td valign="middle" style="font-size:0;line-height:0;"><div style="width:10px;height:10px;background:{LIME};border:1px solid {INK};font-size:0;line-height:0;">&nbsp;</div></td>
        <td style="padding-left:10px;font-family:{SERIF};font-size:24px;color:{INK};letter-spacing:-0.5px;">EmoVoice</td>
        <td style="padding-left:12px;{label}">Nhận diện cảm xúc</td>
      </tr></table>
    </td></tr>
    <tr><td style="padding:36px 32px 0 32px;">
      <div style="{label}">Đặt lại mật khẩu</div>
      <h1 style="margin:10px 0 0 0;font-family:{SERIF};font-weight:400;font-size:36px;line-height:1.1;letter-spacing:-1px;color:{INK};">Mã xác nhận của bạn</h1>
      <p style="margin:16px 0 0 0;font-family:{SANS};font-size:15px;line-height:1.6;color:#36342B;">Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản dùng email này. Nhập mã bên dưới vào trang Quên mật khẩu để tiếp tục.</p>
    </td></tr>
    <tr><td style="padding:28px 32px 0 32px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid {INK};"><tr>
        <td align="center" style="padding:26px 12px 22px 12px;background:{PAPER};">
          <div style="font-family:{MONO};font-size:44px;line-height:1;font-weight:500;letter-spacing:12px;color:{INK};padding-left:12px;">{code}</div>
          <div style="margin:18px auto 0 auto;width:72px;height:4px;background:{LIME};font-size:0;line-height:0;">&nbsp;</div>
        </td>
      </tr></table>
      <div style="margin-top:10px;{label}">Gồm 6 chữ số &nbsp;·&nbsp; có hiệu lực {ttl} phút &nbsp;·&nbsp; dùng một lần</div>
    </td></tr>
    <tr><td style="padding:28px 32px 0 32px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid {RULE};"><tr>
        <td style="padding-top:18px;font-family:{SANS};font-size:13px;line-height:1.6;color:#36342B;">
          <strong style="color:{INK};">Không chia sẻ mã này với bất kỳ ai.</strong> Nhân viên EmoVoice không bao giờ hỏi mã của bạn.<br>
          Nếu không phải bạn yêu cầu, hãy bỏ qua email này: mật khẩu của bạn không bị thay đổi.
        </td>
      </tr></table>
    </td></tr>
    <tr><td style="padding:32px 32px 28px 32px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid {INK};"><tr>
        <td style="padding-top:14px;{label}font-size:10px;">EmoVoice · Khóa luận tốt nghiệp · Kết quả chỉ mang tính tham khảo</td>
      </tr></table>
    </td></tr>
  </table>
</td></tr></table>
</body></html>"""


def build_reset_message(to_email: str, code: str, ttl_minutes: int) -> EmailMessage:
    sender = settings.smtp_from.strip() or settings.smtp_user.strip() or "no-reply@emovoice.local"
    message = EmailMessage()
    message["Subject"] = "EmoVoice – Mã đặt lại mật khẩu"
    message["From"] = sender
    message["To"] = to_email
    message.set_content(
        "Xin chào,\n\n"
        "Hệ thống EmoVoice nhận được yêu cầu đặt lại mật khẩu cho tài khoản dùng email này.\n\n"
        f"Mã đặt lại của bạn: {code}\n\n"
        f"Mã gồm 6 chữ số, có hiệu lực {ttl_minutes} phút và chỉ dùng được một lần. Không chia sẻ mã này với bất kỳ ai.\n"
        "Nếu không phải bạn yêu cầu, hãy bỏ qua email này, mật khẩu của bạn không bị thay đổi.\n"
    )
    message.add_alternative(build_reset_html(code, ttl_minutes), subtype="html")  # ứng dụng email hiện HTML; văn bản thuần là bản dự phòng
    return message


def send_reset_code(to_email: str, code: str, ttl_minutes: int) -> None:
    """Gửi mã đặt lại. MailNotConfigured nếu chưa có SMTP_HOST; MailError nếu gửi lỗi."""
    if not settings.smtp_configured:
        raise MailNotConfigured("Chưa cấu hình SMTP_HOST trong .env.")
    message = build_reset_message(to_email, code, ttl_minutes)
    try:
        if settings.smtp_port == 465:
            client = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=15, context=ssl.create_default_context())
        else:
            client = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15)
        with client:
            if settings.smtp_port != 465:
                client.starttls(context=ssl.create_default_context())  # mã không bao giờ đi qua mạng dưới dạng văn bản thô
            if settings.smtp_user:
                client.login(settings.smtp_user, settings.smtp_password)
            client.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        raise MailError(f"Gửi email thất bại: {type(exc).__name__}") from exc
