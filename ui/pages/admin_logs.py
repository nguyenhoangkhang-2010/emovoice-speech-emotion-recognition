# Admin: nhật ký hệ thống từ bảng system_logs (đăng nhập, đăng ký, khóa tài khoản, đăng ký mô hình...).
# Mọi handler gọi guard_admin.
import logging

import gradio as gr
from sqlalchemy.exc import SQLAlchemyError

from services import admin_service
from ui import i18n_vi as T
from ui import render
from ui.components import daterange, pagination
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
    aware = moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)
    return aware.astimezone().strftime("%H:%M:%S - %d/%m/%Y")


def _table_value(rows):
    if not rows:
        return EMPTY_TABLE
    return [[render.level_chip_html(r["level"]), r["service"], r["message"], r["user"] or "—", _fmt_time(r["created_at"])] for r in rows]


def _fetch(session, page, size, level, service, span, q):
    guard_admin(session)
    level_value = None if level == T.LOG_LEVELS[0] else level
    service_value = None if service == T.LOG_ALL_SERVICES else service
    try:
        date_from, date_to = daterange.parse(span)
        rows, total = admin_service.list_logs(session, page, size, level_value, None, q, service_value, date_from, date_to)
    except ValueError as exc:
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
        span = daterange.build("logs-range", scale=2)
        search = gr.Textbox(placeholder=T.LOG_SEARCH_PH, show_label=False, container=False, elem_classes=["ev-field", "ev-field-search"], scale=4, max_lines=1)
    date_hint = gr.HTML("", elem_classes=["ev-plain"])
    table = gr.Dataframe(headers=HEADERS, datatype=["html", "str", "str", "str", "str"], interactive=False, buttons=[], show_search="none", show_row_numbers=False, max_height=900, elem_id="admin-logs-table", elem_classes=["ev-df"])
    pg = pagination.build()

    extra_inputs = [session_state, level, service, span, search]
    run = pagination.wire(pg, lambda page, size, session, lv, sv, sp, q: _fetch(session, page, size, lv, sv, sp, q), extra_inputs=extra_inputs, extra_outputs=[table])
    all_outputs = pagination.controls(pg) + [table]
    for trigger in (level.change, service.change, span.change, search.submit):
        trigger(lambda size, session, lv, sv, sp, q: run(1, size, session, lv, sv, sp, q), inputs=[pg["size"], *extra_inputs], outputs=all_outputs)

    def load_fn(session):
        guard_admin(session)
        first = None
        try:
            first = admin_service.first_log_date(session)
        except SQLAlchemyError:
            logger.exception("Không đọc được ngày nhật ký đầu tiên")
        return [*run(1, 10, session, T.LOG_LEVELS[0], T.LOG_ALL_SERVICES, "", ""), render.date_hint_html("logs-range", first)]

    return {"load_fn": load_fn, "load_outputs": [*all_outputs, date_hint]}
