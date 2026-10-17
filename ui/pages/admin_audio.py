# Admin — Quản lý dữ liệu âm thanh: mẫu của mọi người dùng, trình phát, lọc, tìm kiếm, xóa (đề cương: "Quản lý dữ liệu").
# CHƯA có khung Stitch — dựng theo style Stitch; chỉ hiện khi ENABLE_ADMIN_EXTRA_PAGES=1. Mọi handler gọi guard_admin.
# Dữ liệu THẬT từ admin_service. Xóa là vĩnh viễn nên phải qua bước xác nhận (bấm "Xóa mẫu đã chọn" -> hỏi lại -> "Xác nhận xóa").
import logging
import os
from datetime import timezone

import gradio as gr
from sqlalchemy.exc import SQLAlchemyError

from ml.config import EMOTION_NAMES
from services import admin_service
from ui import i18n_vi as T
from ui import render
from ui.components import pagination
from ui.pages import guard_admin

logger = logging.getLogger(__name__)

NAME = "admin_audio"
LABEL = T.NAV_ADMIN_AUDIO
GROUP = "admin"
ADMIN_ONLY = True
EXTRA = True

HEADERS = [T.TABLE_COL_FILE, T.COL_USER, T.TABLE_COL_EMOTION, T.COL_ANALYSES, T.TABLE_COL_TIME]
EMOTION_CHOICES = [T.HISTORY_ALL_EMOTIONS] + [T.EMOTION_VI[k] for k in EMOTION_NAMES]
EMPTY_TABLE = [["", "", "", "", ""]]


def _emotion_key(label):
    return next((k for k in EMOTION_NAMES if T.EMOTION_VI[k] == label), None)


def _fmt_duration(seconds: float) -> str:
    return f"{int(seconds // 60):02d}:{seconds % 60:05.2f}"


def _fmt_time(moment) -> str:
    aware = moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)  # SQLite trả datetime không múi giờ (UTC)
    return aware.astimezone().strftime("%H:%M - %d/%m/%Y")


def _emotion_cell(row) -> str:
    if row["emotion"] is None:
        return f'<span class="ev-meta">{render.esc(T.AUDIO_NOT_ANALYZED)}</span>'
    return render.emotion_chip_html(row["emotion"])


def _table_value(rows):
    if not rows:
        return EMPTY_TABLE
    return [
        [render.audio_file_cell_html(r["file"], _fmt_duration(r["duration"])), r["user"], _emotion_cell(r), str(r["predictions"]), _fmt_time(r["uploaded_at"])]
        for r in rows
    ]


def _fetch(session, page, size, q, emotion_label):
    guard_admin(session)
    try:
        rows, total = admin_service.list_all_audio(session, page, size, q, _emotion_key(emotion_label))
    except SQLAlchemyError:
        logger.exception("Không đọc được danh sách âm thanh")
        gr.Warning(T.MSG_DB_ERROR)
        rows, total = [], 0
    return total, [_table_value(rows), rows, None, gr.update(value=None, visible=False), gr.update(visible=False), ""]


def build(session_state):
    rows_state = gr.State([])
    selected = gr.State(None)
    gr.HTML(render.page_header_html(T.ADMIN_AUDIO_EYEBROW, T.ADMIN_AUDIO_TITLE, T.ADMIN_AUDIO_SUB, ""), elem_classes=["ev-plain"])
    with gr.Row(elem_classes=["ev-toolbar"]):
        search = gr.Textbox(placeholder=T.ADMIN_AUDIO_SEARCH_PH, show_label=False, container=False, elem_classes=["ev-field"], scale=4, max_lines=1)
        emotion = gr.Dropdown(EMOTION_CHOICES, value=T.HISTORY_ALL_EMOTIONS, show_label=False, container=False, elem_classes=["ev-field", "ev-select"], scale=2)
    table = gr.Dataframe(headers=HEADERS, datatype=["html", "str", "html", "str", "str"], interactive=False, buttons=[], show_search="none", show_row_numbers=False, max_height=900, wrap=False, elem_id="admin-audio-table", elem_classes=["ev-df"])
    gr.HTML(f'<div class="ev ev-meta">{render.esc(T.ADMIN_SELECT_HINT)}</div>', elem_classes=["ev-plain"])
    player = gr.Audio(label=T.DRAWER_LISTEN_AGAIN, interactive=False, type="filepath", visible=False, buttons=[])
    delete_btn = gr.Button(T.BTN_DELETE_AUDIO, elem_classes=["ev-btn-danger"], scale=0, min_width=220)
    with gr.Row(visible=False) as confirm_row:
        confirm_btn = gr.Button(T.BTN_CONFIRM_DELETE, elem_classes=["ev-btn-danger"], scale=0, min_width=200)
        cancel_btn = gr.Button(T.BTN_CANCEL_DELETE, elem_classes=["ev-btn-outline"], scale=0, min_width=140)
    message = gr.HTML("", elem_classes=["ev-plain"])
    pg = pagination.build()

    # mọi lần nạp lại bảng (lọc, đổi trang, sau khi xóa) đều bỏ chọn dòng, ẩn trình phát và hàng xác nhận
    extra_inputs = [session_state, search, emotion]
    extra_outputs = [table, rows_state, selected, player, confirm_row, message]
    run = pagination.wire(pg, lambda page, size, session, q, e: _fetch(session, page, size, q, e), extra_inputs=extra_inputs, extra_outputs=extra_outputs)
    all_outputs = pagination.controls(pg) + extra_outputs
    for trigger in (search.submit, emotion.change):
        trigger(lambda size, session, q, e: run(1, size, session, q, e), inputs=[pg["size"], *extra_inputs], outputs=all_outputs)

    def on_select(session, rows, evt: gr.SelectData):
        guard_admin(session)
        index = evt.index[0] if isinstance(evt.index, (list, tuple)) else evt.index
        row = rows[index] if rows and index is not None and index < len(rows) else None
        path = row["file_path"] if row and row["file_path"] and os.path.exists(row["file_path"]) else None
        # chọn dòng khác thì hủy yêu cầu xóa đang chờ xác nhận
        return row, gr.update(value=path, visible=path is not None), gr.update(visible=False), ""

    table.select(on_select, inputs=[session_state, rows_state], outputs=[selected, player, confirm_row, message])

    def on_delete(session, row):
        guard_admin(session)
        if not row:
            return gr.update(visible=False), render.message_html(T.MSG_NO_SELECTION)
        question = T.MSG_CONFIRM_DELETE_AUDIO.format(file=row["file"], user=row["user"], n=row["predictions"])
        return gr.update(visible=True), render.message_html(question, "info")

    delete_btn.click(on_delete, inputs=[session_state, selected], outputs=[confirm_row, message])
    cancel_btn.click(lambda: (gr.update(visible=False), ""), outputs=[confirm_row, message])

    unchanged = [gr.update()] * len(all_outputs)

    def on_confirm(session, row, page, size, q, e):
        guard_admin(session)
        if not row:
            return [*unchanged[:-1], render.message_html(T.MSG_NO_SELECTION)]
        try:
            summary = admin_service.delete_audio(session, row["audio_id"])
        except ValueError as exc:  # mẫu đã bị xóa trước đó: nạp lại bảng cho khớp thực tế
            refreshed = run(page, size, session, q, e)
            refreshed[-1] = render.message_html(str(exc))
            return refreshed
        except SQLAlchemyError:
            logger.exception("Không xóa được mẫu âm thanh")
            return [*unchanged[:-1], render.message_html(T.MSG_DB_ERROR)]
        refreshed = run(page, size, session, q, e)  # nạp lại bảng (cũng bỏ chọn dòng, ẩn trình phát và hàng xác nhận)
        refreshed[-1] = render.message_html(T.MSG_AUDIO_DELETED.format(file=summary["file"], user=summary["user"], n=summary["predictions"]), "success")
        return refreshed

    confirm_btn.click(on_confirm, inputs=[session_state, selected, pg["state"], pg["size"], search, emotion], outputs=all_outputs)

    def load_fn(session):
        guard_admin(session)
        return run(1, 10, session, "", T.HISTORY_ALL_EMOTIONS)

    return {"load_fn": load_fn, "load_outputs": all_outputs}
