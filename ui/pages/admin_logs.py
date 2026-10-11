# Admin — Nhật ký hệ thống (UC06). Stitch: qu_n_tr_h_th_ng_emovoice (chỉ có thẻ timeline "Nhật ký hoạt động"; bảng lọc đầy đủ dựng theo style Stitch).
# Mọi handler gọi guard_admin; dữ liệu mẫu cứng cho tới khi admin_service.list_logs được cài đặt.
from typing import List

import gradio as gr

from services import admin_service
from ui import i18n_vi as T
from ui import render
from ui.components import pagination
from ui.pages import guard_admin

NAME = "admin_logs"
LABEL = T.NAV_ADMIN_LOGS
GROUP = "admin"
ADMIN_ONLY = True
EXTRA = False

HEADERS = [T.COL_LEVEL, T.COL_SERVICE, T.COL_MESSAGE, T.COL_USER, T.TABLE_COL_TIME]

# --- dữ liệu mẫu cứng (thay bằng admin_service.list_logs) ---
_SAMPLE = [
    ("INFO", "auth", "Đăng nhập thành công", "demo.user", "14:32:08 - Hôm nay"),
    ("INFO", "inference", "Suy luận hoàn tất trong 7,6 ms", "demo.user", "14:30:41 - Hôm nay"),
    ("WARNING", "preprocess", "Không phát hiện giọng nói rõ ràng (VAD-Null)", "demo.user", "11:15:42 - Hôm nay"),
    ("ERROR", "audio", "Định dạng không được hỗ trợ (UC02-E1)", "demo.user", "09:40:19 - Hôm nay"),
    ("INFO", "model_loader", "Đã nạp best_distilhubert_lora.pt", "—", "08:02:11 - Hôm nay"),
]


def _sample_logs() -> List[dict]:
    return [{"level": lv, "service": sv, "message": msg, "user": user, "time": when} for _ in range(6) for (lv, sv, msg, user, when) in _SAMPLE]


def _table_value(rows):
    return [[render.level_chip_html(r["level"]), r["service"], r["message"], r["user"], r["time"]] for r in rows]


def _fetch(session, page, size, level, q):
    guard_admin(session)
    level_value = None if level == T.LOG_LEVELS[0] else level
    try:
        rows, total = admin_service.list_logs(session, page, size, level_value, None, q)
    except NotImplementedError:
        all_rows = [r for r in _sample_logs() if (not level_value or r["level"] == level_value) and (not q or q.lower() in r["message"].lower())]
        total, rows = len(all_rows), all_rows[(page - 1) * size : page * size]
    return total, [_table_value(rows) if rows else [["", "", "", "", ""]]]


def build(session_state):
    gr.HTML(render.page_header_html(T.ADMIN_LOGS_EYEBROW, T.ADMIN_LOGS_TITLE, T.ADMIN_LOGS_SUB, render.tag_html(T.SAMPLE_DATA_TAG)), elem_classes=["ev-plain"])
    with gr.Row(elem_classes=["ev-toolbar"]):
        level = gr.Dropdown(T.LOG_LEVELS, value=T.LOG_LEVELS[0], show_label=False, container=False, elem_classes=["ev-field", "ev-select"], scale=2)
        search = gr.Textbox(placeholder=T.LOG_SEARCH_PH, show_label=False, container=False, elem_classes=["ev-field"], scale=4, max_lines=1)
    table = gr.Dataframe(headers=HEADERS, datatype=["html", "str", "str", "str", "str"], interactive=False, wrap=True, elem_id="admin-logs-table", elem_classes=["ev-df"])
    pg = pagination.build()

    extra_inputs = [session_state, level, search]
    run = pagination.wire(pg, lambda page, size, session, lv, q: _fetch(session, page, size, lv, q), extra_inputs=extra_inputs, extra_outputs=[table])
    all_outputs = pagination.controls(pg) + [table]
    level.change(lambda size, session, lv, q: run(1, size, session, lv, q), inputs=[pg["size"], *extra_inputs], outputs=all_outputs)
    search.submit(lambda size, session, lv, q: run(1, size, session, lv, q), inputs=[pg["size"], *extra_inputs], outputs=all_outputs)

    def load_fn(session):
        guard_admin(session)
        return run(1, 10, session, T.LOG_LEVELS[0], "")

    return {"load_fn": load_fn, "load_outputs": all_outputs}
