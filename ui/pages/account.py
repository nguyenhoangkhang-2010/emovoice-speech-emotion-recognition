# Tài khoản của tôi (ngoài báo cáo): mỗi người dùng tự sửa họ tên, email và đổi mật khẩu của chính mình.
# Mọi handler lấy người dùng từ phiên (guard_login), không nhận user_id từ giao diện nên không sửa được tài khoản người khác.
import gradio as gr

from services import account_service
from ui import i18n_vi as T
from ui import render
from ui.pages import guard_login

NAME = "account"
LABEL = T.NAV_ACCOUNT
GROUP = "account"
ADMIN_ONLY = False
EXTRA = False


def _section_head(title: str, sub: str) -> str:
    return f'<div class="ev ev-sec-head"><div><h2 class="ev-h3">{render.esc(title)}</h2><p class="ev-meta">{render.esc(sub)}</p></div></div>'


def _password_box(label: str) -> "gr.Textbox":
    return gr.Textbox(label=label, type="password", elem_classes=["ev-field"], max_lines=1)


def build(session_state):
    gr.HTML(render.page_header_html(T.ACCOUNT_EYEBROW, T.ACCOUNT_TITLE, T.ACCOUNT_SUB, ""), elem_classes=["ev-plain"])
    with gr.Row(equal_height=False, elem_classes=["ev-account-main"]):
        with gr.Column(scale=7):
            with gr.Column(elem_classes=["ev-section", "ev-form"]):
                gr.HTML(_section_head(T.ACCOUNT_PROFILE_TITLE, T.ACCOUNT_PROFILE_SUB), elem_classes=["ev-plain"])
                full_name = gr.Textbox(label=T.ACCOUNT_FULL_NAME, placeholder=T.ACCOUNT_FULL_NAME_PH, elem_classes=["ev-field"], max_lines=1)
                email = gr.Textbox(label=T.FIELD_EMAIL, placeholder=T.FIELD_EMAIL_PH, elem_classes=["ev-field"], max_lines=1)
                with gr.Row(elem_classes=["ev-form-row"]):
                    username = gr.Textbox(label=T.FIELD_USERNAME, interactive=False, elem_classes=["ev-field", "ev-field-readonly"], max_lines=1)
                    role = gr.Textbox(label=T.COL_ROLE, interactive=False, elem_classes=["ev-field", "ev-field-readonly"], max_lines=1)
                profile_msg = gr.HTML("", elem_classes=["ev-plain", "ev-msg-slot"])
                save_btn = gr.Button(T.BTN_SAVE_PROFILE, elem_classes=["ev-btn-cta"])
            with gr.Column(elem_classes=["ev-section", "ev-form"]):
                gr.HTML(_section_head(T.ACCOUNT_PASSWORD_TITLE, T.ACCOUNT_PASSWORD_SUB), elem_classes=["ev-plain"])
                current_pw = _password_box(T.ACCOUNT_CURRENT_PASSWORD)
                with gr.Row(elem_classes=["ev-form-row"]):
                    new_pw = _password_box(T.FIELD_NEW_PASSWORD)
                    confirm_pw = _password_box(T.FIELD_CONFIRM_PASSWORD)
                password_msg = gr.HTML("", elem_classes=["ev-plain", "ev-msg-slot"])
                password_btn = gr.Button(T.BTN_CHANGE_PASSWORD, elem_classes=["ev-btn-outline"], scale=0)
        with gr.Column(scale=4, elem_classes=["ev-aside"]):
            summary = gr.HTML("", elem_classes=["ev-plain"])

    def load_fn(session):
        profile = account_service.get_profile(guard_login(session))
        role_text = T.ROLE_ADMIN_VI if profile["role"] == "Admin" else T.ROLE_USER_VI
        return [profile["full_name"], profile["email"], profile["username"], role_text, render.account_summary_html(profile), "", "", "", "", ""]

    load_outputs = [full_name, email, username, role, summary, profile_msg, password_msg, current_pw, new_pw, confirm_pw]

    def on_save(session, name, mail):
        user = guard_login(session)
        try:
            updated = account_service.update_profile(user, name, mail)
        except ValueError as exc:
            return user, render.message_html(str(exc)), gr.update()
        return updated, render.message_html(T.MSG_PROFILE_SAVED, "success"), render.account_summary_html(account_service.get_profile(updated))

    save_event = save_btn.click(on_save, inputs=[session_state, full_name, email], outputs=[session_state, profile_msg, summary])

    def on_change_password(session, current, new, confirm):
        user = guard_login(session)
        try:
            account_service.change_password(user, current, new, confirm)
        except ValueError as exc:
            return render.message_html(str(exc)), gr.update(), gr.update(), gr.update()
        except NotImplementedError as exc:  # bcrypt (UC01) chưa cài nên chưa băm / so khớp mật khẩu được
            return render.message_html(T.MSG_NOT_IMPLEMENTED.format(detail=exc), "info"), gr.update(), gr.update(), gr.update()
        return render.message_html(T.MSG_PASSWORD_CHANGED, "success"), "", "", ""

    password_btn.click(on_change_password, inputs=[session_state, current_pw, new_pw, confirm_pw], outputs=[password_msg, current_pw, new_pw, confirm_pw])
    return {"load_fn": load_fn, "load_outputs": load_outputs, "after_save": save_event}
