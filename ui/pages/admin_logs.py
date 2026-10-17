# Admin — Nhật ký hệ thống (UC06). Stitch: qu_n_tr_h_th_ng_emovoice (chỉ có thẻ timeline "Nhật ký hoạt động"; bảng lọc đầy đủ dựng theo style Stitch).
# Dữ liệu THẬT từ admin_service.list_logs (bảng system_logs: đăng nhập, đăng ký, khóa tài khoản, đăng ký mô hình...). Mọi handler gọi guard_admin.
import logging

import gradio as gr
from sqlalchemy.exc import SQLAlchemyError

from services import admin_service
from ui import i18n_vi as T
from ui import render
from ui.components import pagination
from ui.pages import guard_admin
from datetime import timezone

logger = logging.getLogger(__name__)

NAME = "admin_logs"
LABEL = T.NAV_ADMIN_LOGS
GROUP = "admin"
ADMIN_ONLY = True
EXTRA = False

HEADERS = [T.COL_LEVEL, T.COL_SERVICE, T.COL_MESSAGE, T.COL_USER, T.TABLE_COL_TIME]
EMPTY_TABLE = [["", "", "", "", ""]]


def _fmt_time(moment) -> str:
    aware = moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)  # SQLite trả datetime không múi giờ (UTC)
    return aware.astimezone().strftime("%H:%M:%S - %d/%m/%Y")


def _table_value(rows):
    if not rows:
        return EMPTY_TABLE
    return [[render.level_chip_html(r["level"]), r["service"], r["message"], r["user"] or "—", _fmt_time(r["created_at"])] for r in rows]


def _parse_date(text):
    """Ô ngày nhập năm-tháng-ngày hoặc ngày/tháng/năm -> 'YYYY-MM-DD'; trống -> None. Sai định dạng thì ném ValueError."""
    text = (text or "").strip()
    if not text:
        return None
    if "/" in text:
        parts = text.split("/")
        if len(parts) == 3 and all(p.strip().isdigit() for p in parts):
            return f"{int(parts[2]):04d}-{int(parts[1]):02d}-{int(parts[0]):02d}"
    return text


def _fetch(session, page, size, level, service, day, q):
    guard_admin(session)
    level_value = None if level == T.LOG_LEVELS[0] else level
    service_value = None if service == T.LOG_ALL_SERVICES else service
    try:
        rows, total = admin_service.list_logs(session, page, size, level_value, _parse_date(day), q, service_value)
    except ValueError as exc:  # ngày hoặc mức không hợp lệ
        gr.Warning(str(exc))
        rows, total = [], 0
    except SQLAlchemyError:
        logger.exception("Không đọc được nhật ký hệ thống")
        gr.Warning(T.MSG_DB_ERROR)
        rows, total = [], 0
    return total, [_table_value(rows)]


def build(session_state):
    gr.HTML(render.page_header_html(T.ADMIN_LOGS_EYEBROW, T.ADMIN_LOGS_TITLE, T.ADMIN_LOGS_SUB, ""), elem_classes=["ev-plain"])
    with gr.Row(elem_classes=["ev-toolbar"]):
        level = gr.Dropdown(T.LOG_LEVELS, value=T.LOG_LEVELS[0], show_label=False, container=False, elem_classes=["ev-field", "ev-select"], scale=2)
        service = gr.Dropdown([T.LOG_ALL_SERVICES, *admin_service.LOG_SERVICES], value=T.LOG_ALL_SERVICES, show_label=False, container=False, elem_classes=["ev-field", "ev-select"], scale=2)
        day = gr.Textbox(placeholder=T.LOG_DATE_PH, show_label=False, container=False, elem_classes=["ev-field"], scale=2, max_lines=1)
        search = gr.Textbox(placeholder=T.LOG_SEARCH_PH, show_label=False, container=False, elem_classes=["ev-field"], scale=4, max_lines=1)
    table = gr.Dataframe(headers=HEADERS, datatype=["html", "str", "str", "str", "str"], interactive=False, buttons=[], show_search="none", show_row_numbers=False, max_height=900, elem_id="admin-logs-table", elem_classes=["ev-df"])
    pg = pagination.build()

    extra_inputs = [session_state, level, service, day, search]
    run = pagination.wire(pg, lambda page, size, session, lv, sv, d, q: _fetch(session, page, size, lv, sv, d, q), extra_inputs=extra_inputs, extra_outputs=[table])
    all_outputs = pagination.controls(pg) + [table]
    level.change(lambda size, session, lv, sv, d, q: run(1, size, session, lv, sv, d, q), inputs=[pg["size"], *extra_inputs], outputs=all_outputs)
    day.submit(lambda size, session, lv, sv, d, q: run(1, size, session, lv, sv, d, q), inputs=[pg["size"], *extra_inputs], outputs=all_outputs)
    search.submit(lambda size, session, lv, sv, d, q: run(1, size, session, lv, sv, d, q), inputs=[pg["size"], *extra_inputs], outputs=all_outputs)
    service.change(lambda size, session, lv, sv, d, q: run(1, size, session, lv, sv, d, q), inputs=[pg["size"], *extra_inputs], outputs=all_outputs)

    def load_fn(session):
        guard_admin(session)
        return run(1, 10, session, T.LOG_LEVELS[0], T.LOG_ALL_SERVICES, "", "")

    return {"load_fn": load_fn, "load_outputs": all_outputs}
