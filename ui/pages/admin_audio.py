# Admin — Quản lý dữ liệu âm thanh: mẫu của mọi người dùng, trình phát, lọc, tìm kiếm, xóa (đề cương: "Quản lý dữ liệu").
# CHƯA có khung Stitch — dựng theo style Stitch; chỉ hiện khi ENABLE_ADMIN_EXTRA_PAGES=1. Mọi handler gọi guard_admin.
from typing import List

import gradio as gr

from ml.config import EMOTION_NAMES
from services import admin_service
from ui import i18n_vi as T
from ui import render
from ui.components import pagination
from ui.pages import guard_admin

NAME = "admin_audio"
LABEL = T.NAV_ADMIN_AUDIO
GROUP = "admin"
ADMIN_ONLY = True
EXTRA = True

HEADERS = [T.TABLE_COL_FILE, T.COL_USER, T.TABLE_COL_EMOTION, T.TABLE_COL_TIME]
EMOTION_CHOICES = [T.HISTORY_ALL_EMOTIONS] + [T.EMOTION_VI[k] for k in EMOTION_NAMES]


def _sample_audio() -> List[dict]:
    # --- dữ liệu mẫu cứng (thay bằng admin_service.list_all_audio) ---
    return [
        {"audio_id": i, "file": f"mau_am_thanh_{i:02d}.wav", "duration": "00:03.00", "user": f"user{i % 4 + 1}", "emotion": EMOTION_NAMES[i % 8], "time": "14:25 - 24/10/2024", "path": None}
        for i in range(1, 31)
    ]


def _table_value(rows):
    return [[render.audio_file_cell_html(r["file"], r["duration"]), r["user"], render.emotion_chip_html(r["emotion"]), r["time"]] for r in rows]


def _fetch(session, page, size, q, emotion_label):
    guard_admin(session)
    emo = None if emotion_label == T.HISTORY_ALL_EMOTIONS else emotion_label
    try:
        rows, total = admin_service.list_all_audio(session, page, size, q, emo)
    except NotImplementedError:
        keys = [k for k in EMOTION_NAMES if T.EMOTION_VI[k] == emo]
        all_rows = [r for r in _sample_audio() if (not q or q.lower() in r["file"].lower() or q.lower() in r["user"].lower()) and (not emo or r["emotion"] in keys)]
        total, rows = len(all_rows), all_rows[(page - 1) * size : page * size]
    return total, [_table_value(rows) if rows else [["", "", "", ""]], rows, None]


def build(session_state):
    rows_state = gr.State([])
    selected = gr.State(None)
    gr.HTML(render.page_header_html(T.ADMIN_AUDIO_EYEBROW, T.ADMIN_AUDIO_TITLE, T.ADMIN_AUDIO_SUB, render.tag_html(T.SAMPLE_DATA_TAG)), elem_classes=["ev-plain"])
    with gr.Row(elem_classes=["ev-toolbar"]):
        search = gr.Textbox(placeholder=T.ADMIN_AUDIO_SEARCH_PH, show_label=False, container=False, elem_classes=["ev-field"], scale=4, max_lines=1)
        emotion = gr.Dropdown(EMOTION_CHOICES, value=T.HISTORY_ALL_EMOTIONS, show_label=False, container=False, elem_classes=["ev-field", "ev-select"], scale=2)
    table = gr.Dataframe(headers=HEADERS, datatype=["html", "str", "html", "str"], interactive=False, buttons=[], show_search="none", show_row_numbers=False, max_height=900, wrap=False, elem_id="admin-audio-table", elem_classes=["ev-df"])
    gr.HTML(f'<div class="ev ev-meta">{render.esc(T.ADMIN_SELECT_HINT)}</div>', elem_classes=["ev-plain"])
    player = gr.Audio(label="Nghe lại", interactive=False, type="filepath", elem_classes=["ev-audio"])
    with gr.Row():
        delete_btn = gr.Button(T.BTN_DELETE_AUDIO, elem_classes=["ev-btn-danger"], scale=0, min_width=220)
        message = gr.HTML("", elem_classes=["ev-plain"])
    pg = pagination.build()

    extra_inputs = [session_state, search, emotion]
    run = pagination.wire(pg, lambda page, size, session, q, e: _fetch(session, page, size, q, e), extra_inputs=extra_inputs, extra_outputs=[table, rows_state, selected])
    all_outputs = pagination.controls(pg) + [table, rows_state, selected]
    for trigger in (search.submit, emotion.change):
        trigger(lambda size, session, q, e: run(1, size, session, q, e), inputs=[pg["size"], *extra_inputs], outputs=all_outputs)

    def on_select(session, rows, evt: gr.SelectData):
        guard_admin(session)
        index = evt.index[0] if isinstance(evt.index, (list, tuple)) else evt.index
        row = rows[index] if rows and index is not None and index < len(rows) else None
        return row, (row or {}).get("path")

    table.select(on_select, inputs=[session_state, rows_state], outputs=[selected, player])

    def on_delete(session, row):
        guard_admin(session)
        if not row:
            return render.message_html(T.MSG_NO_SELECTION)
        try:
            admin_service.delete_audio(session, row["audio_id"])
        except NotImplementedError as exc:
            return render.message_html(T.MSG_ADMIN_NOT_IMPLEMENTED.format(detail=exc), "info")
        return render.message_html(T.MSG_DONE, "success")

    delete_btn.click(on_delete, inputs=[session_state, selected], outputs=message)

    def load_fn(session):
        guard_admin(session)
        return run(1, 10, session, "", T.HISTORY_ALL_EMOTIONS)

    return {"load_fn": load_fn, "load_outputs": all_outputs}
