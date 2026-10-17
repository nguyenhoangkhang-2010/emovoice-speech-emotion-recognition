# Đăng nhập | Đăng ký | Quên mật khẩu (UC01). Stitch: ng_nh_p_ng_k_emovoice_desktop (đăng nhập + tab Đăng ký).
# Panel "Quên mật khẩu" CHƯA có khung Stitch: dựng theo style Stitch. Nút "Ghi nhớ đăng nhập" chỉ là khung (TODO: cookie phiên).
# Mọi nghiệp vụ nằm ở services/auth_service; trang chỉ hiện lại thông báo của service và lỗi kết nối CSDL.
import gradio as gr
from sqlalchemy.exc import SQLAlchemyError

from core.config import settings
from core.session import SessionUser
from services import auth_service, mail_service
from ui import i18n_vi as T
from ui import render


def dev_session(role: str) -> SessionUser:
    """Phiên giả cho nút 'Vào thử'; kiểm tra lại cờ ở phía server (không tin việc nút có hiện hay không)."""
    if not settings.dev_bypass_login:
        raise gr.Error(T.MSG_DENIED)
    if role == "Admin":
        return SessionUser(user_id=0, username="demo.admin", email="demo.admin@emovoice.local", role="Admin", display_name="Quản trị viên (dev)")
    return SessionUser(user_id=-1, username="demo.user", email="demo.user@emovoice.local", role="User", display_name="Người dùng (dev)")


def handle_dev_user():
    return dev_session("User"), ""


def handle_dev_admin():
    return dev_session("Admin"), ""


def handle_login(username: str, password: str, remember: bool):
    """-> (SessionUser | None, html thông báo)"""
    if not username or not password:
        return None, render.message_html(T.MSG_FILL_ALL)
    try:
        return auth_service.login(username.strip(), password), ""
    except ValueError as exc:  # sai tài khoản/mật khẩu, tài khoản bị khóa, đăng nhập sai quá nhiều lần
        return None, render.message_html(str(exc))
    except SQLAlchemyError:
        return None, render.message_html(T.MSG_DB_ERROR)


def _handle_register(username, email, password, confirm):
    if not all([username, email, password, confirm]):
        return render.message_html(T.MSG_FILL_ALL), False
    if password != confirm:
        return render.message_html(T.MSG_PASSWORD_MISMATCH), False
    try:
        auth_service.register(username.strip(), email.strip(), password, confirm)
    except ValueError as exc:
        return render.message_html(str(exc)), False
    except SQLAlchemyError:
        return render.message_html(T.MSG_DB_ERROR), False
    return render.message_html(T.MSG_REGISTER_DONE, "success"), True


def _handle_send_reset(email):
    if not email:
        return render.message_html(T.MSG_FILL_ALL), False
    try:
        code = auth_service.request_password_reset(email.strip())
    except mail_service.MailNotConfigured:
        return render.message_html(T.MSG_MAIL_NOT_CONFIGURED), False
    except SQLAlchemyError:
        return render.message_html(T.MSG_DB_ERROR), False
    text = T.MSG_RESET_SENT.format(minutes=settings.password_reset_ttl_minutes)
    if code:  # chỉ có khi bật RESET_CODE_ON_SCREEN=1 (demo, không an toàn)
        text += " " + T.MSG_RESET_DEMO_CODE.format(code=code)
    return render.message_html(text, "info"), True


def _handle_verify_code(email, code):
    if not code:
        return render.message_html(T.MSG_FILL_ALL), False
    try:
        auth_service.verify_reset_code(email.strip(), code.strip())
    except ValueError as exc:
        return render.message_html(str(exc)), False
    except SQLAlchemyError:
        return render.message_html(T.MSG_DB_ERROR), False
    return "", True


def _handle_reset(email, code, new_password, confirm):
    if not all([email, code, new_password, confirm]):
        return render.message_html(T.MSG_FILL_ALL), False
    if new_password != confirm:
        return render.message_html(T.MSG_PASSWORD_MISMATCH), False
    try:
        auth_service.reset_password(email.strip(), code.strip(), new_password)
    except ValueError as exc:
        return render.message_html(str(exc)), False
    except SQLAlchemyError:
        return render.message_html(T.MSG_DB_ERROR), False
    return render.message_html(T.MSG_RESET_DONE, "success"), True


def _toggle_password(shown: bool):
    shown = not shown
    return shown, gr.update(type="text" if shown else "password"), gr.update(value="visibility" if shown else "visibility_off")


def _field(label, placeholder="", password=False, icon=None):
    classes = ["ev-field"] + ([f"ev-field-{icon}"] if icon else [])
    if not password:
        return gr.Textbox(label=label, placeholder=placeholder, type="text", elem_classes=classes, max_lines=1)
    with gr.Column(elem_classes=["ev-pw"]):  # ô mật khẩu kèm nút mắt hiện/ẩn như Stitch
        box = gr.Textbox(label=label, placeholder=placeholder, type="password", elem_classes=classes + ["ev-field-pw"], max_lines=1)
        eye = gr.Button("visibility_off", elem_classes=["ev-eye"], variant="secondary", scale=0, min_width=0)
        shown = gr.State(False)
        eye.click(_toggle_password, inputs=[shown], outputs=[shown, box, eye])
    return box


def build(session_state):
    with gr.Column(visible=True, elem_id="view-auth") as view:
        with gr.Row(elem_id="auth-nav"):
            gr.HTML(render.login_navbar_html(), elem_classes=["ev-plain"])
            with gr.Row(elem_id="auth-nav-links"):
                nav_about = gr.Button(T.LOGIN_NAV_ABOUT, elem_classes=["ev-navlink"], variant="secondary", scale=0, min_width=0)
                nav_guide = gr.Button(T.LOGIN_NAV_GUIDE, elem_classes=["ev-navlink"], variant="secondary", scale=0, min_width=0)
                nav_login = gr.Button(T.TAB_LOGIN, elem_classes=["ev-navcta"], variant="secondary", scale=0, min_width=0)
        with gr.Row(elem_id="auth-body") as body_auth:
            with gr.Column(elem_id="auth-left", scale=1):
                gr.HTML(render.login_hero_html(), elem_classes=["ev-plain"])
            with gr.Column(elem_id="auth-right", scale=1):
                with gr.Column(elem_id="auth-card"):
                    with gr.Row(elem_id="auth-switch") as switch:
                        tab_login = gr.Button(T.TAB_LOGIN, elem_classes=["ev-seg-btn", "active"], variant="primary")
                        tab_register = gr.Button(T.TAB_REGISTER, elem_classes=["ev-seg-btn"], variant="secondary")

                    # --- Đăng nhập ---
                    with gr.Column(visible=True) as panel_login:
                        gr.HTML(render.auth_title_html(T.LOGIN_TITLE, T.LOGIN_SUB), elem_classes=["ev-plain"])
                        login_user = _field(T.FIELD_USERNAME, T.FIELD_USERNAME_PH, icon="user")
                        login_pass = _field(T.FIELD_PASSWORD, T.FIELD_PASSWORD_PH, password=True, icon="lock")
                        login_msg = gr.HTML("", elem_classes=["ev-plain", "ev-msg-slot"])  # lỗi nằm ngay dưới ô mật khẩu như Stitch
                        with gr.Row(elem_classes=["ev-remember-row"]):
                            remember = gr.Checkbox(label=T.REMEMBER_ME, value=True, scale=1)
                            forgot_link = gr.Button(T.FORGOT_LINK, elem_classes=["ev-btn-link"], variant="secondary", scale=0, min_width=0)
                        login_btn = gr.Button(T.BTN_LOGIN, variant="primary", elem_classes=["ev-btn-primary"])
                        dev_user = dev_admin = None
                        if settings.dev_bypass_login:
                            gr.HTML(f'<div class="ev ev-meta">{render.esc(T.DEV_BYPASS_NOTE)}</div>', elem_classes=["ev-plain"])
                            with gr.Row():
                                dev_user = gr.Button(T.BTN_DEV_USER, elem_classes=["ev-btn-outline"])
                                dev_admin = gr.Button(T.BTN_DEV_ADMIN, elem_classes=["ev-btn-outline"])
                        gr.HTML('<div class="ev-auth-divider"></div>', elem_classes=["ev-plain"])
                        with gr.Row(elem_classes=["ev-auth-foot"]):
                            gr.HTML(f'<span class="ev ev-sub">{render.esc(T.NO_ACCOUNT)}</span>', elem_classes=["ev-plain"])
                            goto_register = gr.Button(T.BTN_GOTO_REGISTER, elem_classes=["ev-btn-link"], variant="secondary", scale=0, min_width=0)

                    # --- Đăng ký ---
                    with gr.Column(visible=False) as panel_register:
                        gr.HTML(render.auth_title_html(T.REGISTER_TITLE, T.REGISTER_SUB), elem_classes=["ev-plain"])
                        reg_user = _field(T.FIELD_USERNAME, T.FIELD_USERNAME_PH, icon="user")
                        reg_email = _field(T.FIELD_EMAIL, T.FIELD_EMAIL_PH, icon="mail")
                        reg_pass = _field(T.FIELD_PASSWORD, T.FIELD_PASSWORD_PH, password=True, icon="lock")
                        reg_confirm = _field(T.FIELD_CONFIRM_PASSWORD, "", password=True, icon="lock")
                        reg_msg = gr.HTML("", elem_classes=["ev-plain"])
                        reg_btn = gr.Button(T.BTN_REGISTER, variant="primary", elem_classes=["ev-btn-primary"])

                    # --- Quên mật khẩu (chưa có Stitch): 3 bước. 1 nhập email -> 2 nhập mã 6 số -> 3 đặt mật khẩu mới (chỉ hiện khi mã đúng) ---
                    with gr.Column(visible=False) as panel_forgot:
                        gr.HTML(render.auth_title_html(T.FORGOT_TITLE, ""), elem_classes=["ev-plain"])
                        with gr.Column(visible=True) as forgot_step1:
                            gr.HTML(f'<div class="ev ev-sub">{render.esc(T.FORGOT_SUB_STEP1)}</div>', elem_classes=["ev-plain"])
                            fg_email = _field(T.FIELD_EMAIL, T.FIELD_EMAIL_PH, icon="mail")
                            fg_send = gr.Button(T.BTN_SEND_RESET, variant="primary", elem_classes=["ev-btn-primary"])
                        with gr.Column(visible=False) as forgot_step2:
                            gr.HTML(f'<div class="ev ev-sub">{render.esc(T.FORGOT_SUB_STEP2)}</div>', elem_classes=["ev-plain"])
                            fg_code = _field(T.FIELD_RESET_CODE, T.FIELD_RESET_CODE_PH)
                            fg_verify = gr.Button(T.BTN_VERIFY_CODE, variant="primary", elem_classes=["ev-btn-primary"])
                        with gr.Column(visible=False) as forgot_step3:
                            gr.HTML(f'<div class="ev ev-sub">{render.esc(T.FORGOT_SUB_STEP3)}</div>', elem_classes=["ev-plain"])
                            fg_new = _field(T.FIELD_NEW_PASSWORD, "", password=True)
                            fg_confirm = _field(T.FIELD_CONFIRM_PASSWORD, "", password=True)
                            fg_reset = gr.Button(T.BTN_RESET, variant="primary", elem_classes=["ev-btn-primary"])
                        fg_msg = gr.HTML("", elem_classes=["ev-plain"])
                        back_login = gr.Button(T.BTN_BACK_TO_LOGIN, elem_classes=["ev-btn-link"], variant="secondary")

        # --- Trang công khai: Giới thiệu / Hướng dẫn (chưa có Stitch) ---
        with gr.Column(visible=False, elem_id="public-about") as page_about:
            gr.HTML(render.about_page_html, elem_classes=["ev-plain"])  # hàm: chạy lại mỗi lần tải trang để số đo mô hình luôn mới
            about_cta = gr.Button(T.PUBLIC_CTA, elem_classes=["ev-btn-primary", "ev-btn-fit"], variant="primary", scale=0)
        with gr.Column(visible=False, elem_id="public-guide") as page_guide:
            gr.HTML(render.guide_page_html(settings.max_upload_mb), elem_classes=["ev-plain"])
            guide_cta = gr.Button(T.PUBLIC_CTA, elem_classes=["ev-btn-primary", "ev-btn-fit"], variant="primary", scale=0)
        gr.HTML(render.app_footer_html(), elem_classes=["ev-plain"])

    # ---- chuyển trang công khai: đăng nhập / giới thiệu / hướng dẫn ----
    public_outputs = [body_auth, page_about, page_guide, nav_about, nav_guide]

    def show_public(mode: str):
        def link(on):
            return gr.update(elem_classes=["ev-navlink", "active"] if on else ["ev-navlink"])

        return [gr.update(visible=mode == "login"), gr.update(visible=mode == "about"), gr.update(visible=mode == "guide"), link(mode == "about"), link(mode == "guide")]

    # ---- chuyển panel ----
    panel_outputs = [panel_login, panel_register, panel_forgot, switch, tab_login, tab_register]

    def show_panel(mode: str):
        def active(on):
            return gr.update(variant="primary" if on else "secondary", elem_classes=["ev-seg-btn", "active"] if on else ["ev-seg-btn"])

        return [
            gr.update(visible=mode == "login"),
            gr.update(visible=mode == "register"),
            gr.update(visible=mode == "forgot"),
            gr.update(visible=mode != "forgot"),
            active(mode == "login"),
            active(mode == "register"),
        ]

    tab_login.click(lambda: show_panel("login"), outputs=panel_outputs)
    back_login.click(lambda: show_panel("login"), outputs=panel_outputs)
    tab_register.click(lambda: show_panel("register"), outputs=panel_outputs)
    goto_register.click(lambda: show_panel("register"), outputs=panel_outputs)
    forgot_link.click(lambda: show_panel("forgot"), outputs=panel_outputs)

    nav_about.click(lambda: show_public("about"), outputs=public_outputs)
    nav_guide.click(lambda: show_public("guide"), outputs=public_outputs)
    for _btn in (nav_login, about_cta, guide_cta):  # về lại trang đăng nhập
        _btn.click(lambda: [*show_public("login"), *show_panel("login")], outputs=[*public_outputs, *panel_outputs])

    # ---- đăng ký ----
    def on_register(username, email, password, confirm):
        message, ok = _handle_register(username, email, password, confirm)
        # thành công: chuyển về đăng nhập và hiện lời xác nhận ngay dưới ô mật khẩu (panel đăng ký đã ẩn nên không thấy được ở đó)
        return [("" if ok else message), (message if ok else gr.update()), *(show_panel("login") if ok else [gr.update()] * 6)]

    reg_btn.click(on_register, inputs=[reg_user, reg_email, reg_pass, reg_confirm], outputs=[reg_msg, login_msg, *panel_outputs])

    # ---- quên mật khẩu: bước 1 (gửi mã) -> bước 2 (xác nhận mã) -> bước 3 (mật khẩu mới) ----
    steps = [forgot_step1, forgot_step2, forgot_step3]

    def show_step(n: int):
        return [gr.update(visible=i == n) for i in range(3)]

    def on_send(email):
        message, ok = _handle_send_reset(email)
        return [message, *(show_step(1) if ok else [gr.update()] * 3)]

    fg_send.click(on_send, inputs=[fg_email], outputs=[fg_msg, *steps])

    def on_verify(email, code):
        message, ok = _handle_verify_code(email, code)
        return [message, *(show_step(2) if ok else [gr.update()] * 3)]

    fg_verify.click(on_verify, inputs=[fg_email, fg_code], outputs=[fg_msg, *steps])

    def on_reset(email, code, new_password, confirm):
        message, ok = _handle_reset(email, code, new_password, confirm)
        if ok:  # xong: về màn đăng nhập, quay lại bước 1 cho lần sau
            return [(""), message, *show_step(0), *show_panel("login")]
        return [message, gr.update(), *[gr.update()] * 3, *[gr.update()] * 6]

    fg_reset.click(on_reset, inputs=[fg_email, fg_code, fg_new, fg_confirm], outputs=[fg_msg, login_msg, *steps, *panel_outputs])

    return {
        "view": view,
        "login_user": login_user,
        "login_pass": login_pass,
        "remember": remember,
        "login_btn": login_btn,
        "login_msg": login_msg,
        "dev_user": dev_user,
        "dev_admin": dev_admin,
        "forms": [login_user, login_pass, reg_user, reg_email, reg_pass, reg_confirm, fg_email, fg_code, fg_new, fg_confirm],
    }
