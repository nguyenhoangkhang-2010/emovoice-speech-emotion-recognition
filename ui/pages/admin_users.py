# Admin — Quản lý người dùng (UC06). Stitch: qu_n_tr_h_th_ng_emovoice (bảng "Quản lý người dùng hệ thống" + ô tìm kiếm + nút Thêm).
# Công tắc bật/tắt của Stitch không đặt được trong gr.Dataframe: chọn dòng rồi bấm nút "Khóa / mở khóa". Mọi handler gọi guard_admin.
# Dữ liệu THẬT từ admin_service. Thêm nút "Cấp mật khẩu tạm" cho người quên mật khẩu mà không có email.
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
            render.role_chip_html(r["role"]),
            f'{r["usage"]:,}',
            render.state_chip_html(r["active"]),
        ]
        for r in rows
    ]


def _fetch(session, page, size, q):
    guard_admin(session)
    try:
        rows, total = admin_service.list_users(session, page, size, q)
    except SQLAlchemyError:
        logger.exception("Không đọc được danh sách người dùng")
        gr.Warning(T.MSG_DB_ERROR)
        rows, total = [], 0
    return total, [_table_value(rows), rows, None, gr.update(value=None, interactive=False)]  # bỏ chọn dòng; ô vai trò trống và khóa tới khi chọn dòng khác


def build(session_state):
    rows_state = gr.State([])
    selected = gr.State(None)
    gr.HTML(render.page_header_html(T.ADMIN_USERS_EYEBROW, T.ADMIN_USERS_TITLE, T.ADMIN_USERS_SUB, ""), elem_classes=["ev-plain"])
    with gr.Row(elem_classes=["ev-toolbar"]):
        search = gr.Textbox(placeholder=T.ADMIN_USERS_SEARCH_PH, show_label=False, container=False, elem_classes=["ev-field"], scale=4, max_lines=1)
        add_btn = gr.Button(f"+ {T.BTN_ADD_USER}", elem_classes=["ev-btn-tint"], scale=0, min_width=120)
    table = gr.Dataframe(headers=HEADERS, datatype=["html", "str", "html", "str", "html"], interactive=False, buttons=[], show_search="none", show_row_numbers=False, max_height=900, wrap=False, elem_id="admin-users-table", elem_classes=["ev-df"])
    gr.HTML(f'<div class="ev ev-meta">{render.esc(T.ADMIN_SELECT_HINT)}</div>', elem_classes=["ev-plain"])
    role_select = gr.Dropdown(
        choices=[(T.ROLE_USER_VI, "User"), (T.ROLE_ADMIN_VI, "Admin")], value=None, label=T.LABEL_ROLE_SELECT, interactive=False,  # chỉ dùng được khi đã chọn một dòng
        elem_classes=["ev-field", "ev-select", "ev-field-narrow"], scale=0,
    )
    with gr.Row():
        toggle_btn = gr.Button(T.BTN_TOGGLE_USER, elem_classes=["ev-btn-outline"], scale=0, min_width=300)
        reset_btn = gr.Button(T.BTN_RESET_USER_PASSWORD, elem_classes=["ev-btn-outline"], scale=0, min_width=240)
    message = gr.HTML("", elem_classes=["ev-plain"])
    pg = pagination.build()

    extra_inputs = [session_state, search]
    run = pagination.wire(pg, lambda page, size, session, q: _fetch(session, page, size, q), extra_inputs=extra_inputs, extra_outputs=[table, rows_state, selected, role_select])
    all_outputs = pagination.controls(pg) + [table, rows_state, selected, role_select]
    search.submit(lambda size, session, q: run(1, size, session, q), inputs=[pg["size"], *extra_inputs], outputs=all_outputs)

    def on_select(session, rows, evt: gr.SelectData):
        guard_admin(session)
        index = evt.index[0] if isinstance(evt.index, (list, tuple)) else evt.index
        row = rows[index] if rows and index is not None and index < len(rows) else None
        return row, gr.update(value=row["role"] if row else None, interactive=row is not None)  # hiện đúng vai trò hiện tại của dòng vừa chọn

    table.select(on_select, inputs=[session_state, rows_state], outputs=[selected, role_select])

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
        return [render.message_html(text, "success"), *run(page, size, session, q)]  # nạp lại bảng để thấy trạng thái mới

    toggle_btn.click(on_toggle, inputs=action_inputs, outputs=[message, *all_outputs])

    def on_role(session, user, new_role, page, size, q):
        """Chọn vai trò trong ô chọn là áp dụng ngay (sự kiện input chỉ chạy khi NGƯỜI DÙNG đổi, không chạy khi hệ thống đặt giá trị lúc chọn dòng)."""
        guard_admin(session)

        def keep(text, kind="error"):  # không đổi gì, trả ô chọn về vai trò hiện tại của dòng đã chọn
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
    # TODO UC06: thêm tài khoản (admin tạo) — chưa có khung Stitch cho form này.
    add_btn.click(lambda session: (guard_admin(session), gr.Info("TODO UC06: thêm tài khoản chưa được cài đặt."))[1], inputs=session_state)

    def load_fn(session):
        guard_admin(session)
        return run(1, 10, session, "")

    return {"load_fn": load_fn, "load_outputs": all_outputs}
