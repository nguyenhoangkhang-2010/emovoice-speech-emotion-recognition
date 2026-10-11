# Lịch sử phân tích (UC05) + drawer chi tiết XAI. Stitch: l_ch_s_ph_n_t_ch_c_m_x_c.
# Bảng là gr.Dataframe (datatype html) thay cho <table> tùy biến; chọn dòng mở drawer (Column visible) thay cho cột phải sticky.
# Skeleton: history_service chưa cài đặt nên dùng dữ liệu mẫu cứng _sample_rows() (có lọc/tìm/phân trang để xem giao diện).
from typing import List

import gradio as gr

from services import history_service
from ui import i18n_vi as T
from ui import render
from ui.components import pagination
from ml.config import EMOTION_NAMES

NAME = "history"
LABEL = T.NAV_HISTORY
GROUP = "analysis"
ADMIN_ONLY = False
EXTRA = False

_SEED = [
    ("cuoc_goi_khachhang_08.wav", "00:03.42", "angry", 96.8, "14:25 - 24/10/2024"),
    ("hoi_thoai_tuvan_14.wav", "00:04.10", "happy", 91.2, "13:48 - 24/10/2024"),
    ("khao_sat_y_kien_02.wav", "00:02.55", "neutral", 88.5, "11:12 - 24/10/2024"),
    ("phan_nan_dichvu_09.wav", "00:05.18", "sad", 94.1, "09:40 - 24/10/2024"),
    ("phan_ung_dotngot_03.wav", "00:03.04", "surprised", 85.0, "08:15 - 24/10/2024"),
]
_EXTRA_EMOTIONS = ["calm", "fearful", "disgust"]
EMOTION_CHOICES = [T.HISTORY_ALL_EMOTIONS] + [T.EMOTION_VI[k] for k in EMOTION_NAMES]
TABLE_HEADERS = [T.TABLE_COL_FILE, T.TABLE_COL_EMOTION, T.TABLE_COL_CONFIDENCE, T.TABLE_COL_MODEL, T.TABLE_COL_TIME]


def _sample_rows() -> List[dict]:
    """48 bản ghi mẫu (bằng số kết quả minh họa của Stitch) — dữ liệu giả, không đại diện kết quả thật."""
    rows = []
    for i in range(48):
        name, dur, emo, conf, when = _SEED[i % 5]
        if i % 7 == 6:
            emo = _EXTRA_EMOTIONS[(i // 7) % 3]
        rows.append({"id": i + 1, "file": name.replace(".wav", f"_{i + 1:02d}.wav"), "duration": dur, "emotion": emo, "confidence": round(conf - (i % 5) * 1.3, 1), "model": "DistilHuBERT", "time": when, "days_ago": i // 4})
    return rows


def _sample_query(q, emotion_label, time_label):
    rows = _sample_rows()
    if q:
        rows = [r for r in rows if q.lower() in r["file"].lower()]
    if emotion_label and emotion_label != T.HISTORY_ALL_EMOTIONS:
        keys = [k for k in EMOTION_NAMES if T.EMOTION_VI[k] == emotion_label]
        rows = [r for r in rows if r["emotion"] in keys]
    days = {T.HISTORY_TIME_CHOICES[0]: 7, T.HISTORY_TIME_CHOICES[1]: 30}.get(time_label)
    if days:
        rows = [r for r in rows if r["days_ago"] < days]
    return rows


def _sample_probs(emotion: str, confidence: float) -> List[float]:
    top = EMOTION_NAMES.index(emotion)
    rest = (100.0 - confidence) / 7.0
    return [confidence / 100.0 if i == top else rest / 100.0 for i in range(8)]


def _table_value(rows: List[dict]):
    return [
        [render.audio_file_cell_html(r["file"], r["duration"]), render.emotion_chip_html(r["emotion"]), render.confidence_cell_html(r["confidence"]), r["model"], r["time"]]
        for r in rows
    ]


def _fetch(page, size, q, emotion_label, time_label):
    try:
        rows, total = history_service.list_history(None, page, size, emotion_label, None, q)  # TODO UC05: truyền session thật
        avg = sum(r["confidence"] for r in rows) / len(rows) if rows else 0.0  # TODO UC05: độ tin cậy TB toàn bộ kết quả lọc
    except NotImplementedError:
        all_rows = _sample_query(q, emotion_label, time_label)
        total = len(all_rows)
        rows = all_rows[(page - 1) * size : page * size]
        avg = sum(r["confidence"] for r in all_rows) / total if total else 0.0
    summary = render.summary_badges_html([(T.HISTORY_TOTAL, f"{total:,}", "#4361D8"), (T.HISTORY_AVG_CONF, f"{avg:.1f}%", "#1FA89A")])
    table_value = _table_value(rows) if rows else [["", "", "", "", ""]]
    return total, [table_value, rows, summary, gr.update(visible=total == 0), gr.update(visible=total != 0), gr.update(visible=False)]


def build(session_state):
    rows_state = gr.State([])
    gr.HTML(
        render.page_header_html(T.HISTORY_EYEBROW, T.HISTORY_TITLE, T.HISTORY_SUB),
        elem_classes=["ev-plain"],
    )
    summary = gr.HTML("", elem_classes=["ev-plain"])
    with gr.Row(elem_classes=["ev-toolbar"]):
        search = gr.Textbox(placeholder=T.HISTORY_SEARCH_PH, show_label=False, container=False, elem_classes=["ev-field"], scale=4, max_lines=1)
        emotion = gr.Dropdown(EMOTION_CHOICES, value=T.HISTORY_ALL_EMOTIONS, show_label=False, container=False, elem_classes=["ev-field", "ev-select"], scale=2)
        timef = gr.Dropdown(T.HISTORY_TIME_CHOICES, value=T.HISTORY_TIME_CHOICES[1], show_label=False, container=False, elem_classes=["ev-field", "ev-select"], scale=2)
        export_btn = gr.Button(T.BTN_EXPORT, elem_classes=["ev-btn-outline"], scale=0, min_width=170)
        goto_analyze = gr.Button(T.BTN_NEW_ANALYSIS, elem_classes=["ev-btn-cta", "ev-btn-sm"], scale=0, min_width=150)
    with gr.Row(equal_height=False):
        with gr.Column(scale=8):
            with gr.Column(visible=True) as table_col:
                table = gr.Dataframe(
                    headers=TABLE_HEADERS, datatype=["html", "html", "html", "str", "str"], interactive=False, wrap=True,
                    elem_id="history-table", elem_classes=["ev-df"],
                )
                gr.HTML(f'<div class="ev ev-meta">{render.esc(T.HISTORY_SELECT_HINT)}</div>', elem_classes=["ev-plain"])
                pg = pagination.build()
            with gr.Column(visible=False) as empty_col:
                gr.HTML(render.empty_state_html("graphic_eq", T.EMPTY_HISTORY_TITLE, T.EMPTY_HISTORY_TEXT), elem_classes=["ev-plain"])
                goto_analyze_empty = gr.Button(T.BTN_START_NOW, elem_classes=["ev-btn-outline"], scale=0, min_width=220)
        with gr.Column(scale=4, visible=False, elem_id="history-drawer") as drawer:
            drawer_head = gr.HTML("", elem_classes=["ev-plain"])
            drawer_audio = gr.Audio(label="Nghe lại", interactive=False, type="filepath", elem_classes=["ev-audio-mic"])
            drawer_heat = gr.HTML("", elem_classes=["ev-plain"])
            drawer_probs = gr.HTML("", elem_classes=["ev-plain"])
            with gr.Row():
                close_btn = gr.Button(T.BTN_CLOSE_DRAWER, elem_classes=["ev-btn-outline"])
                json_btn = gr.Button(T.BTN_DOWNLOAD_JSON, elem_classes=["ev-btn-cta", "ev-btn-sm"])

    extra_inputs = [search, emotion, timef]
    extra_outputs = [table, rows_state, summary, empty_col, table_col, drawer]
    run = pagination.wire(pg, _fetch, extra_inputs=extra_inputs, extra_outputs=extra_outputs)
    all_outputs = pagination.controls(pg) + extra_outputs
    for trigger in (search.submit, emotion.change, timef.change):
        trigger(lambda size, q, e, t: run(1, size, q, e, t), inputs=[pg["size"], *extra_inputs], outputs=all_outputs)

    def on_select(rows, evt: gr.SelectData):
        index = evt.index[0] if isinstance(evt.index, (list, tuple)) else evt.index
        if not rows or index is None or index >= len(rows):
            return [gr.update(visible=False), "", None, "", ""]
        r = rows[index]
        levels = [(i * 7 + r["id"]) % 5 for i in range(12)]  # TODO UC05: lấy mức attention thật từ heatmap đã lưu
        return [
            gr.update(visible=True),
            render.drawer_head_html(r["file"], T.DRAWER_META.format(duration=r["duration"]), r["emotion"], r["confidence"]),
            None,
            render.mini_heatmap_html(levels),
            render.prob_bars_compact_html(_sample_probs(r["emotion"], r["confidence"])),
        ]

    drawer_outputs = [drawer, drawer_head, drawer_audio, drawer_heat, drawer_probs]
    table.select(on_select, inputs=[rows_state], outputs=drawer_outputs)
    close_btn.click(lambda: gr.update(visible=False), outputs=drawer)
    # TODO UC05/XAI: xuất báo cáo JSON và xuất Excel (đề cương thang điểm mục 6).
    json_btn.click(lambda: gr.Info("TODO UC05: tải báo cáo JSON chưa được cài đặt."))
    export_btn.click(lambda: gr.Info("TODO UC05: xuất Excel chưa được cài đặt."))

    def load_fn(session):
        return run(1, 10, "", T.HISTORY_ALL_EMOTIONS, T.HISTORY_TIME_CHOICES[1])

    return {
        "load_fn": load_fn,
        "load_outputs": all_outputs,
        "goto_analyze": goto_analyze,
        "goto_analyze_empty": goto_analyze_empty,
    }
