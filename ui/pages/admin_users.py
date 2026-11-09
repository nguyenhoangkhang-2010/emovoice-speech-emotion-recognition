# Admin: quản lý người dùng (tìm kiếm, khóa/mở khóa, đổi vai trò, cấp mật khẩu tạm, xóa, thêm tài khoản). Mọi handler gọi guard_admin.
# gr.Dataframe không đặt được công tắc bật/tắt: chọn dòng rồi bấm nút.
import logging

import gradio as gr
from sqlalchemy.exc import SQLAlchemyError

from services import admin_service
from ui import i18n_vi as T
from ui import render
from ui.components import pagination
from ui.pages import guard_admin

logger = logging.getLogger(__name__)

NAME = "admin_users"
LABEL = T.NAV_ADMIN_USERS
GROUP = "admin"
ADMIN_ONLY = True
EXTRA = False

HEADERS = [T.COL_USERNAME, T.COL_EMAIL, T.COL_ROLE, T.COL_USAGE, T.COL_ACTIVE]
EMPTY_TABLE = [["", "", "", "", ""]]


def _table_value(rows):
    if not rows:
        return EMPTY_TABLE
    return [
        [
            f'<div class="ev-file-cell"><div class="ev-avatar">{render.initials(r["full_name"] or r["username"])}</div>'
            f'<div><div class="ev-file-name">{render.esc(r["full_name"] or r["username"])}</div><div class="ev-meta">@{render.esc(r["username"])}</div></div></div>',
            r["email"],
            render.role_chip_html(r["role"], r.get("is_system_admin", False)),
            f'{r["usage"]:,}',
            render.state_chip_html(r["active"]),
        ]
        for r in rows
    ]


ROLE_CHOICES = [(T.ROLE_USER_VI, "User"), (T.ROLE_ADMIN_VI, "Admin")]


def create_user_action(session, username, email, full_name, role):
    """Xử lý popup "Thêm tài khoản": (html thông báo, đã tạo?). Lỗi nhập liệu hiện đúng câu của dịch vụ; lỗi CSDL hiện thông báo chung."""
    guard_admin(session)
    if not (username or "").strip() or not (email or "").strip():
        return render.message_html(T.MSG_FILL_ALL), False
    try:
        created = admin_service.create_user(session, username, email, role or "User", full_name or "")
    except ValueError as exc:
        return render.message_html(str(exc)), False
    except SQLAlchemyError:
        logger.exception("Không tạo được tài khoản")
        return render.message_html(T.MSG_DB_ERROR), False
    return render.temp_password_html(created["username"], created["temp_password"]), True


def _fetch(session, page, size, q):
    guard_admin(session)
    try:
        rows, total = admin_service.list_users(session, page, size, q)
    except SQLAlchemyError:
        logger.exception("Không đọc được danh sách người dùng")
        gr.Warning(T.MSG_DB_ERROR)
        rows, total = [], 0
    return total, [_table_value(rows), rows, None, gr.update(visible=False), gr.update(value=None, interactive=False)]  # bỏ chọn dòng, đóng popup xóa; ô vai trò trống và khóa tới khi chọn dòng khác


def build(session_state):
    rows_state = gr.State([])
    selected = gr.State(None)
    gr.HTML(render.page_header_html(T.ADMIN_USERS_EYEBROW, T.ADMIN_USERS_TITLE, T.ADMIN_USERS_SUB, ""), elem_classes=["ev-plain"])
    with gr.Row(elem_classes=["ev-toolbar"]):
        search = gr.Textbox(placeholder=T.ADMIN_USERS_SEARCH_PH, show_label=False, container=False, elem_classes=["ev-field", "ev-field-search"], scale=4, max_lines=1)
        add_btn = gr.Button(f"+ {T.BTN_ADD_USER}", elem_classes=["ev-btn-tint"], scale=0, min_width=120)
    table = gr.Dataframe(headers=HEADERS, datatype=["html", "str", "html", "str", "html"], interactive=False, buttons=[], show_search="none", show_row_numbers=False, max_height=900, wrap=False, elem_id="admin-users-table", elem_classes=["ev-df"])
    gr.HTML(f'<div class="ev ev-meta">{render.esc(T.ADMIN_SELECT_HINT)}</div>', elem_classes=["ev-plain"])
    role_select = gr.Dropdown(
        choices=[(T.ROLE_USER_VI, "User"), (T.ROLE_ADMIN_VI, "Admin")], value=None, label=T.LABEL_ROLE_SELECT, info=T.ADMIN_ROLE_HINT_LOCKED, interactive=False,
        elem_classes=["ev-field", "ev-select", "ev-field-narrow"], scale=0,
    )
    with gr.Row():
        toggle_btn = gr.Button(T.BTN_TOGGLE_USER, elem_classes=["ev-btn-outline"], scale=0, min_width=300)
        reset_btn = gr.Button(T.BTN_RESET_USER_PASSWORD, elem_classes=["ev-btn-outline"], scale=0, min_width=240)
        delete_btn = gr.Button(T.BTN_DELETE_USER, elem_classes=["ev-btn-danger"], scale=0, min_width=240)
    # popup xác nhận xóa: đóng bằng nút Hủy / Esc / bấm nền mờ (script trong ui/theme.py bấm nút .ev-modal-close)
    with gr.Column(visible=False, elem_classes=["ev-modal"], elem_id="delete-user-modal") as delete_modal:
        with gr.Column(elem_classes=["ev-modal-card"]):
            gr.HTML(render.page_header_html(T.ADMIN_USERS_EYEBROW, T.MODAL_DELETE_USER_TITLE, "", "").replace("ev-page-header", "ev-modal-head"), elem_classes=["ev-plain"])
            delete_question = gr.HTML("", elem_classes=["ev-plain"])
            with gr.Row(elem_classes=["ev-modal-actions"]):
                cancel_btn = gr.Button(T.BTN_CANCEL_DELETE, elem_classes=["ev-btn-outline", "ev-modal-close"], scale=0, min_width=140)
                confirm_btn = gr.Button(T.BTN_CONFIRM_DELETE, elem_classes=["ev-btn-danger"], scale=0, min_width=200)
    message = gr.HTML("", elem_classes=["ev-plain"])
    pg = pagination.build()

    extra_inputs = [session_state, search]
    run = pagination.wire(pg, lambda page, size, session, q: _fetch(session, page, size, q), extra_inputs=extra_inputs, extra_outputs=[table, rows_state, selected, delete_modal, role_select])
    all_outputs = pagination.controls(pg) + [table, rows_state, selected, delete_modal, role_select]
    search.submit(lambda size, session, q: run(1, size, session, q), inputs=[pg["size"], *extra_inputs], outputs=all_outputs)

    def on_select(session, rows, evt: gr.SelectData):
        guard_admin(session)
        index = evt.index[0] if isinstance(evt.index, (list, tuple)) else evt.index
        row = rows[index] if rows and index is not None and index < len(rows) else None
        can_change = row is not None and not row.get("is_system_admin") and row["user_id"] != session.user_id  # admin hệ thống không ai đổi được; không tự đổi vai trò của mình
        return row, gr.update(visible=False), gr.update(value=row["role"] if row else None, interactive=can_change), ""  # chọn dòng khác thì đóng popup xóa nếu đang mở và xóa thông báo cũ

    table.select(on_select, inputs=[session_state, rows_state], outputs=[selected, delete_modal, role_select, message])

    unchanged = [gr.update()] * len(all_outputs)
    action_inputs = [session_state, selected, pg["state"], pg["size"], search]

    def on_toggle(session, user, page, size, q):
        guard_admin(session)
        if not user:
            return [render.message_html(T.MSG_NO_SELECTION), *unchanged]
        try:
            admin_service.set_user_status(session, user["user_id"], not user["active"])
        except ValueError as exc:
            return [render.message_html(str(exc)), *unchanged]
        except SQLAlchemyError:
            logger.exception("Không đổi được trạng thái tài khoản")
            return [render.message_html(T.MSG_DB_ERROR), *unchanged]
        text = (T.MSG_USER_LOCKED if user["active"] else T.MSG_USER_UNLOCKED).format(name=user["username"])
        return [render.message_html(text, "success"), *run(page, size, session, q)]

    toggle_btn.click(on_toggle, inputs=action_inputs, outputs=[message, *all_outputs])

    def on_role(session, user, new_role, page, size, q):
        """Chọn vai trò trong ô chọn là áp dụng ngay (sự kiện input chỉ chạy khi NGƯỜI DÙNG đổi, không chạy khi hệ thống đặt giá trị lúc chọn dòng)."""
        guard_admin(session)

        def keep(text, kind="error"):
            return [render.message_html(text, kind), *unchanged[:-1], gr.update(value=user["role"] if user else None)]

        if not user:
            # Gradio có thể gửi sự kiện đổi ô chọn hai lần cho một lần bấm: lần thừa đến sau khi lần đầu đã đổi xong và bỏ chọn dòng,
            # nên bỏ qua âm thầm để không đè mất thông báo thành công (ô chọn đã bị khóa khi chưa chọn dòng nên đây không phải thao tác của người dùng)
            return [gr.update(), *unchanged]
        try:
            changed = admin_service.set_user_role(session, user["user_id"], new_role)
        except ValueError as exc:
            return keep(str(exc))
        except SQLAlchemyError:
            logger.exception("Không đổi được vai trò tài khoản")
            return keep(T.MSG_DB_ERROR)
        if not changed:
            return keep(T.MSG_ROLE_SAME, "info")
        text = (T.MSG_ROLE_GRANTED if new_role == "Admin" else T.MSG_ROLE_REVOKED).format(name=user["username"])
        return [render.message_html(text, "success"), *run(page, size, session, q)]

    def on_delete(session, user):
        """[popup, câu hỏi trong popup, thông báo trên trang]: lý do không xóa được hiện trên trang, không mở popup."""
        guard_admin(session)
        hidden = gr.update(visible=False)
        if not user:
            return hidden, "", render.message_html(T.MSG_NO_SELECTION)
        if user["user_id"] == session.user_id:
            return hidden, "", render.message_html(admin_service.MSG_SELF_DELETE)
        if user.get("is_system_admin"):
            return hidden, "", render.message_html(admin_service.MSG_SYSTEM_ADMIN_PROTECTED)
        return gr.update(visible=True), render.message_html(T.MSG_CONFIRM_DELETE_USER.format(name=user["username"]), "info"), ""

    delete_btn.click(on_delete, inputs=[session_state, selected], outputs=[delete_modal, delete_question, message])
    cancel_btn.click(lambda: gr.update(visible=False), outputs=delete_modal)

    def on_confirm_delete(session, user, page, size, q):
        guard_admin(session)
        close = list(unchanged)
        close[all_outputs.index(delete_modal)] = gr.update(visible=False)  # xác nhận xong (thành công hay lỗi) đều đóng popup; kết quả hiện ở thông báo trên trang
        if not user:
            return [render.message_html(T.MSG_NO_SELECTION), *close]
        try:
            summary = admin_service.delete_user(session, user["user_id"])
        except ValueError as exc:  # tài khoản đã bị xóa trước đó hoặc không được phép xóa: nạp lại bảng cho khớp thực tế
            return [render.message_html(str(exc)), *run(page, size, session, q)]
        except SQLAlchemyError:
            logger.exception("Không xóa được tài khoản")
            return [render.message_html(T.MSG_DB_ERROR), *close]
        text = T.MSG_USER_DELETED.format(name=summary["username"], audio=summary["audio_files"], n=summary["predictions"])
        return [render.message_html(text, "success"), *run(page, size, session, q)]

    confirm_btn.click(on_confirm_delete, inputs=action_inputs, outputs=[message, *all_outputs])

    role_select.input(on_role, inputs=[session_state, selected, role_select, pg["state"], pg["size"], search], outputs=[message, *all_outputs])

    def on_reset(session, user, page, size, q):
        guard_admin(session)
        if not user:
            return [render.message_html(T.MSG_NO_SELECTION), *unchanged]
        try:
            temp = admin_service.reset_user_password(session, user["user_id"])
        except ValueError as exc:
            return [render.message_html(str(exc)), *unchanged]
        except SQLAlchemyError:
            logger.exception("Không cấp được mật khẩu tạm")
            return [render.message_html(T.MSG_DB_ERROR), *unchanged]
        return [render.message_html(T.MSG_TEMP_PASSWORD.format(name=user["username"], password=temp), "success"), *run(page, size, session, q)]

    reset_btn.click(on_reset, inputs=action_inputs, outputs=[message, *all_outputs])

    # ---- popup "Thêm tài khoản": đóng bằng nút Đóng / Esc / bấm nền mờ (script trong ui/theme.py) ----
    # Kết quả (lỗi hoặc mật khẩu tạm) nằm ngay dưới tiêu đề để luôn thấy dù cửa sổ thấp.
    with gr.Column(visible=False, elem_classes=["ev-modal"], elem_id="add-user-modal") as modal:
        with gr.Column(elem_classes=["ev-modal-card"]):
            gr.HTML(render.page_header_html(T.ADMIN_USERS_EYEBROW, T.MODAL_ADD_USER_TITLE, T.MODAL_ADD_USER_SUB, "").replace("ev-page-header", "ev-modal-head"), elem_classes=["ev-plain"])
            modal_msg = gr.HTML("", elem_classes=["ev-plain"])
            with gr.Column(elem_classes=["ev-modal-form"]) as form_col:
                new_username = gr.Textbox(label=T.FIELD_USERNAME, placeholder=T.FIELD_USERNAME_PH, max_lines=1, elem_classes=["ev-field"])
                new_email = gr.Textbox(label=T.FIELD_EMAIL, placeholder=T.FIELD_EMAIL_PH, max_lines=1, elem_classes=["ev-field"])
                new_name = gr.Textbox(label=T.FIELD_FULL_NAME_OPTIONAL, placeholder=T.ACCOUNT_FULL_NAME_PH, max_lines=1, elem_classes=["ev-field"])
                new_role = gr.Radio(choices=ROLE_CHOICES, value="User", label=T.COL_ROLE, elem_classes=["ev-radio"])
            with gr.Row(elem_classes=["ev-modal-actions"]):
                close_btn = gr.Button(T.BTN_CLOSE_MODAL, elem_classes=["ev-btn-outline", "ev-modal-close"], scale=0, min_width=140)
                create_btn = gr.Button(T.BTN_CREATE_USER, elem_classes=["ev-btn-cta"], scale=0, min_width=220)
                again_btn = gr.Button(T.BTN_ADD_ANOTHER, elem_classes=["ev-btn-cta"], scale=0, min_width=320, visible=False)
    fields = [new_username, new_email, new_name, new_role]
    modal_views = [modal, modal_msg, form_col, create_btn, again_btn]

    def form_view(visible_form):
        """[form_col, create_btn, again_btn]: đang nhập (form + nút Tạo) hoặc đã tạo xong (chỉ kết quả + nút Thêm tài khoản khác)."""
        return [gr.update(visible=visible_form), gr.update(visible=visible_form), gr.update(visible=not visible_form)]

    def open_modal(session):
        guard_admin(session)
        return [gr.update(visible=True), "", *form_view(True), "", "", "", "User"]

    add_btn.click(open_modal, inputs=session_state, outputs=[*modal_views, *fields])
    close_btn.click(lambda: gr.update(visible=False), outputs=modal)
    again_btn.click(lambda: ["", *form_view(True)], outputs=[modal_msg, form_col, create_btn, again_btn])

    def on_create(session, username, email, full_name, role, page, size, q):
        message_html, created = create_user_action(session, username, email, full_name, role)
        if not created:
            return [message_html, *form_view(True), *unchanged, *[gr.update()] * len(fields)]
        return [message_html, *form_view(False), *run(page, size, session, q), "", "", "", "User"]

    create_btn.click(on_create, inputs=[session_state, *fields, pg["state"], pg["size"], search], outputs=[modal_msg, form_col, create_btn, again_btn, *all_outputs, *fields])

    def load_fn(session):
        guard_admin(session)
        return run(1, 10, session, "")

    return {"load_fn": load_fn, "load_outputs": all_outputs}
