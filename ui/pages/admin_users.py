# Admin — Quản lý người dùng (UC06). Stitch: qu_n_tr_h_th_ng_emovoice (bảng "Quản lý người dùng hệ thống" + ô tìm kiếm + nút Thêm).
# Công tắc bật/tắt của Stitch không đặt được trong gr.Dataframe: chọn dòng rồi bấm nút "Khóa / mở khóa". Mọi handler gọi guard_admin.
from typing import List

import gradio as gr

from services import admin_service
from ui import i18n_vi as T
from ui import render
from ui.components import pagination
from ui.pages import guard_admin

NAME = "admin_users"
LABEL = T.NAV_ADMIN_USERS
GROUP = "admin"
ADMIN_ONLY = True
EXTRA = False

HEADERS = [T.COL_USERNAME, T.COL_EMAIL, T.COL_ROLE, T.COL_USAGE, T.COL_ACTIVE]

# --- dữ liệu mẫu cứng (thay bằng admin_service.list_users) ---
_SAMPLE_USERS = [
    {"user_id": 1, "username": "Nguyễn Hoài An", "email": "hoaian.nguyen@emovoice.vn", "role": "Admin", "usage": 14820, "active": True},
    {"user_id": 2, "username": "Lê Thị Thanh Lan", "email": "thanhlan.le@emovoice.vn", "role": "User", "usage": 9340, "active": True},
    {"user_id": 3, "username": "Phạm Hoàng Quân", "email": "hoangquan.pham@emovoice.vn", "role": "User", "usage": 6120, "active": True},
    {"user_id": 4, "username": "Đỗ Văn Minh", "email": "minh.do@emovoice.vn", "role": "Admin", "usage": 8910, "active": True},
    {"user_id": 5, "username": "Trương Bảo Ngọc", "email": "baongoc.truong@emovoice.vn", "role": "User", "usage": 2100, "active": False},
]


def _sample_users() -> List[dict]:
    rows = [dict(u) for u in _SAMPLE_USERS]
    for i in range(6, 24):
        rows.append({"user_id": i, "username": f"Người dùng mẫu {i}", "email": f"user{i}@emovoice.vn", "role": "User", "usage": 100 * i, "active": i % 5 != 0})
    return rows


def _table_value(rows):
    return [
        [f'<div class="ev-file-cell"><div class="ev-avatar">{render.initials(r["username"])}</div><span class="ev-file-name">{render.esc(r["username"])}</span></div>',
         r["email"], render.role_chip_html(r["role"]), f'{r["usage"]:,}', render.state_chip_html(r["active"])]
        for r in rows
    ]


def _fetch(session, page, size, q):
    guard_admin(session)
    try:
        rows, total = admin_service.list_users(session, page, size, q)
    except NotImplementedError:
        all_rows = [r for r in _sample_users() if not q or q.lower() in r["username"].lower() or q.lower() in r["email"].lower()]
        total, rows = len(all_rows), all_rows[(page - 1) * size : page * size]
    return total, [_table_value(rows) if rows else [["", "", "", "", ""]], rows, None]


def build(session_state):
    rows_state = gr.State([])
    selected = gr.State(None)
    gr.HTML(render.page_header_html(T.ADMIN_USERS_EYEBROW, T.ADMIN_USERS_TITLE, T.ADMIN_USERS_SUB, render.tag_html(T.SAMPLE_DATA_TAG)), elem_classes=["ev-plain"])
    with gr.Row(elem_classes=["ev-toolbar"]):
        search = gr.Textbox(placeholder=T.ADMIN_USERS_SEARCH_PH, show_label=False, container=False, elem_classes=["ev-field"], scale=4, max_lines=1)
        add_btn = gr.Button(f"+ {T.BTN_ADD_USER}", elem_classes=["ev-btn-tint"], scale=0, min_width=120)
    table = gr.Dataframe(headers=HEADERS, datatype=["html", "str", "html", "str", "html"], interactive=False, buttons=[], show_search="none", show_row_numbers=False, max_height=900, wrap=False, elem_id="admin-users-table", elem_classes=["ev-df"])
    gr.HTML(f'<div class="ev ev-meta">{render.esc(T.ADMIN_SELECT_HINT)}</div>', elem_classes=["ev-plain"])
    with gr.Row():
        toggle_btn = gr.Button(T.BTN_TOGGLE_USER, elem_classes=["ev-btn-outline"], scale=0, min_width=300)
        message = gr.HTML("", elem_classes=["ev-plain"])
    pg = pagination.build()

    extra_inputs = [session_state, search]
    run = pagination.wire(pg, lambda page, size, session, q: _fetch(session, page, size, q), extra_inputs=extra_inputs, extra_outputs=[table, rows_state, selected])
    all_outputs = pagination.controls(pg) + [table, rows_state, selected]
    search.submit(lambda size, session, q: run(1, size, session, q), inputs=[pg["size"], *extra_inputs], outputs=all_outputs)

    def on_select(session, rows, evt: gr.SelectData):
        guard_admin(session)
        index = evt.index[0] if isinstance(evt.index, (list, tuple)) else evt.index
        return rows[index] if rows and index is not None and index < len(rows) else None

    table.select(on_select, inputs=[session_state, rows_state], outputs=selected)

    def on_toggle(session, user):
        guard_admin(session)
        if not user:
            return render.message_html(T.MSG_NO_SELECTION)
        try:
            admin_service.set_user_status(session, user["user_id"], not user["active"])
        except NotImplementedError as exc:
            return render.message_html(T.MSG_ADMIN_NOT_IMPLEMENTED.format(detail=exc), "info")
        return render.message_html(T.MSG_DONE, "success")

    toggle_btn.click(on_toggle, inputs=[session_state, selected], outputs=message)
    # TODO UC06: thêm tài khoản (admin tạo) — chưa có khung Stitch cho form này.
    add_btn.click(lambda session: (guard_admin(session), gr.Info("TODO UC06: thêm tài khoản chưa được cài đặt."))[1], inputs=session_state)

    def load_fn(session):
        guard_admin(session)
        return run(1, 10, session, "")

    return {"load_fn": load_fn, "load_outputs": all_outputs}
