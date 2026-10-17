# Lịch sử phân tích (UC05) + drawer chi tiết XAI. Stitch: l_ch_s_ph_n_t_ch_c_m_x_c.
# Bảng là gr.Dataframe (datatype html) thay cho <table> tùy biến; chọn dòng mở drawer (Column visible) thay cho cột phải sticky.
# Dữ liệu THẬT từ history_service: chỉ bản ghi của chính người dùng đăng nhập. Drawer hiện ảnh XAI đã lưu lúc phân tích,
# nghe lại tệp gốc và tải báo cáo JSON; nút xuất tải toàn bộ kết quả khớp bộ lọc dạng CSV (Excel mở được).
import json
import logging
import os
import tempfile
from datetime import timezone
from pathlib import Path
from typing import List, Optional

import gradio as gr
from sqlalchemy.exc import SQLAlchemyError

from ml.config import EMOTION_NAMES
from services import history_service
from ui import i18n_vi as T
from ui import render
from ui.components import pagination
from ui.pages import guard_login

logger = logging.getLogger(__name__)

NAME = "history"
LABEL = T.NAV_HISTORY
GROUP = "analysis"
ADMIN_ONLY = False
EXTRA = False

EMOTION_CHOICES = [T.HISTORY_ALL_EMOTIONS] + [T.EMOTION_VI[k] for k in EMOTION_NAMES]
TABLE_HEADERS = [T.TABLE_COL_FILE, T.TABLE_COL_EMOTION, T.TABLE_COL_CONFIDENCE, T.TABLE_COL_MODEL, T.TABLE_COL_TIME, T.TABLE_COL_ACTIONS]
EMPTY_TABLE = [["", "", "", "", "", ""]]


def _emotion_key(label: Optional[str]) -> Optional[str]:
    """Nhãn tiếng Việt trong ô chọn -> tên nhãn tiếng Anh; 'Tất cả' hoặc rỗng -> None (không lọc)."""
    return next((k for k in EMOTION_NAMES if T.EMOTION_VI[k] == label), None)


def _days(label: Optional[str]) -> Optional[int]:
    return {T.HISTORY_TIME_CHOICES[0]: 7, T.HISTORY_TIME_CHOICES[1]: 30}.get(label)


def _fmt_duration(seconds: float) -> str:
    return f"{int(seconds // 60):02d}:{seconds % 60:05.2f}"


def _fmt_time(moment) -> str:
    """Giờ địa phương của máy chủ, dạng 'HH:MM - dd/mm/yyyy'. SQLite trả datetime không múi giờ (UTC)."""
    aware = moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)
    return aware.astimezone().strftime("%H:%M - %d/%m/%Y")


def _export_dir() -> Path:
    path = Path(tempfile.gettempdir()) / "emovoice_exports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _header(total: int, avg_pct: float) -> str:
    badges = render.summary_badges_html([(T.HISTORY_TOTAL, f"{total:,}", "#DDB677"), (T.HISTORY_AVG_CONF, f"{avg_pct:.1f}%", "#62CDB0")])
    return render.page_header_html(T.HISTORY_EYEBROW, T.HISTORY_TITLE, T.HISTORY_SUB, badges)


def _table_value(rows: List[dict]):
    if not rows:
        return EMPTY_TABLE
    return [
        [
            render.audio_file_cell_html(r["file"], _fmt_duration(r["duration"])),
            render.emotion_chip_html(r["emotion"]),
            render.confidence_cell_html(r["confidence"] * 100),
            render.model_chip_html(r["model"]),
            _fmt_time(r["created_at"]),
            render.row_actions_html(),
        ]
        for r in rows
    ]


def _detail_empty():
    """Giá trị cho [drawer, head, audio, xai_title, xai_image, probs, json_btn]."""
    return [gr.update(visible=False), "", gr.update(value=None, visible=False), "", gr.update(value=None, visible=False), "", gr.update(value=None, interactive=False)]


def _write_json(detail: dict) -> str:
    """Báo cáo JSON của một lượt phân tích (không chứa đường dẫn tệp trên máy chủ)."""
    report = {
        "id": detail["id"],
        "file": detail["file"],
        "duration_seconds": round(detail["duration"], 3),
        "emotion": detail["emotion"],
        "confidence": round(detail["confidence"], 4),
        "model": detail["model"],
        "created_at": detail["created_at"].isoformat(),
        "probabilities": {name: round(p, 4) for name, p in zip(EMOTION_NAMES, detail["probs"])},
    }
    path = _export_dir() / f"emovoice_analysis_{detail['id']}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def _detail(session, prediction_id: int):
    detail = history_service.get_history_detail(session, prediction_id)
    if detail is None:
        return _detail_empty()
    audio = detail["audio_path"] if detail["audio_path"] and os.path.exists(detail["audio_path"]) else None
    heat = detail["heatmap_path"] if detail["heatmap_path"] and os.path.exists(detail["heatmap_path"]) else None
    return [
        gr.update(visible=True),
        render.drawer_head_html(detail["file"], T.DRAWER_META.format(duration=_fmt_duration(detail["duration"])), detail["emotion"], detail["confidence"] * 100),
        gr.update(value=audio, visible=audio is not None),
        f'<div class="ev ev-mini-head"><span class="ev-meta-strong">{render.esc(T.DRAWER_HEATMAP)}</span><span class="ev-meta">{render.esc(T.DRAWER_HEATMAP_TAG)}</span></div>' if heat else "",
        gr.update(value=heat, visible=heat is not None),
        render.prob_bars_compact_html(detail["probs"]),
        gr.update(value=_write_json(detail), interactive=True),
    ]


def _fetch(page, size, session, q, emotion_label, time_label):
    guard_login(session)
    key, days = _emotion_key(emotion_label), _days(time_label)
    try:
        rows, total = history_service.list_history(session, page, size, key, days, q)
        summary = history_service.summarize_history(session, key, days, q)
        detail = _detail(session, rows[0]["id"]) if rows else _detail_empty()  # luôn hiện chi tiết dòng đầu như Stitch
        csv_path = _export_dir() / f"emovoice_history_{session.user_id}.csv"
        csv_path.write_text(history_service.export_history_csv(session, key, days, q), encoding="utf-8")
        export = gr.update(value=str(csv_path), interactive=total > 0)
    except SQLAlchemyError:
        logger.exception("Không đọc được lịch sử phân tích")
        gr.Warning(T.MSG_DB_ERROR)
        rows, total, summary, detail, export = [], 0, {"avg_confidence": 0.0}, _detail_empty(), gr.update(value=None, interactive=False)
    outputs = [_table_value(rows), rows, _header(total, summary["avg_confidence"] * 100), render.table_head_html(len(rows), total), gr.update(visible=total == 0), gr.update(visible=total != 0), *detail, export]
    return total, outputs


def build(session_state):
    rows_state = gr.State([])
    header = gr.HTML(_header(0, 0.0), elem_classes=["ev-plain"])
    with gr.Row(elem_classes=["ev-toolbar"]):
        search = gr.Textbox(placeholder=T.HISTORY_SEARCH_PH, show_label=False, container=False, elem_classes=["ev-field", "ev-field-search"], scale=4, max_lines=1)
        emotion = gr.Dropdown(EMOTION_CHOICES, value=T.HISTORY_ALL_EMOTIONS, show_label=False, container=False, elem_classes=["ev-field", "ev-select"], scale=2)
        timef = gr.Dropdown(T.HISTORY_TIME_CHOICES, value=T.HISTORY_TIME_CHOICES[1], show_label=False, container=False, elem_classes=["ev-field", "ev-select"], scale=2)
        export_btn = gr.DownloadButton(T.BTN_EXPORT, elem_id="hist-export", elem_classes=["ev-btn-outline"], scale=0, min_width=170, interactive=False)
        goto_analyze = gr.Button(T.BTN_NEW_ANALYSIS, elem_id="hist-new", elem_classes=["ev-btn-cta", "ev-btn-sm"], scale=0, min_width=150)
    with gr.Row(equal_height=False, elem_classes=["ev-hist-main"]):
        with gr.Column(scale=8):
            with gr.Column(visible=True, elem_classes=["ev-table-card"]) as table_col:
                table_head = gr.HTML(render.table_head_html(0, 0), elem_classes=["ev-plain"])
                table = gr.Dataframe(
                    headers=TABLE_HEADERS, datatype=["html", "html", "html", "html", "str", "html"], interactive=False,
                    buttons=[], show_search="none", show_row_numbers=False, max_height=900, wrap=False, column_widths=["27%", "15%", "10%", "13%", "22%", "13%"],
                    elem_id="history-table", elem_classes=["ev-df"],
                )
                gr.HTML(f'<div class="ev ev-meta ev-select-hint">{render.esc(T.HISTORY_SELECT_HINT)}</div>', elem_classes=["ev-plain"])
                pg = pagination.build()
            with gr.Column(visible=False) as empty_col:
                gr.HTML(render.empty_state_html("graphic_eq", T.EMPTY_HISTORY_TITLE, T.EMPTY_HISTORY_TEXT), elem_classes=["ev-plain"])
                goto_analyze_empty = gr.Button(T.BTN_START_NOW, elem_classes=["ev-btn-outline"], scale=0, min_width=220)
        with gr.Column(scale=4, visible=False, elem_id="history-drawer") as drawer:
            drawer_head = gr.HTML("", elem_classes=["ev-plain"])
            drawer_audio = gr.Audio(label=T.DRAWER_LISTEN_AGAIN, interactive=False, type="filepath", visible=False, buttons=[])
            drawer_xai_title = gr.HTML("", elem_classes=["ev-plain"])
            drawer_xai = gr.Image(show_label=False, container=False, interactive=False, type="filepath", visible=False, buttons=[], elem_classes=["ev-xai-image"])
            drawer_probs = gr.HTML("", elem_classes=["ev-plain"])
            with gr.Row(elem_classes=["ev-drawer-actions"]):
                close_btn = gr.Button(T.BTN_CLOSE_DRAWER, elem_classes=["ev-btn-tint"], scale=0, min_width=0)
                json_btn = gr.DownloadButton(T.BTN_DOWNLOAD_JSON, elem_id="hist-json", elem_classes=["ev-btn-cta", "ev-btn-sm"], scale=0, min_width=0, interactive=False)

    drawer_outputs = [drawer, drawer_head, drawer_audio, drawer_xai_title, drawer_xai, drawer_probs, json_btn]
    extra_inputs = [session_state, search, emotion, timef]
    extra_outputs = [table, rows_state, header, table_head, empty_col, table_col, *drawer_outputs, export_btn]
    run = pagination.wire(pg, _fetch, extra_inputs=extra_inputs, extra_outputs=extra_outputs)
    all_outputs = pagination.controls(pg) + extra_outputs
    for trigger in (search.submit, emotion.change, timef.change):
        trigger(lambda size, s, q, e, t: run(1, size, s, q, e, t), inputs=[pg["size"], *extra_inputs], outputs=all_outputs)

    def on_select(rows, session, evt: gr.SelectData):
        guard_login(session)
        index = evt.index[0] if isinstance(evt.index, (list, tuple)) else evt.index
        if not rows or index is None or index >= len(rows):
            return _detail_empty()
        try:
            return _detail(session, rows[index]["id"])
        except SQLAlchemyError:
            logger.exception("Không đọc được chi tiết bản ghi")
            gr.Warning(T.MSG_DB_ERROR)
            return _detail_empty()

    table.select(on_select, inputs=[rows_state, session_state], outputs=drawer_outputs)
    close_btn.click(lambda: gr.update(visible=False), outputs=drawer)

    def load_fn(session):
        return run(1, 10, session, "", T.HISTORY_ALL_EMOTIONS, T.HISTORY_TIME_CHOICES[1])

    return {
        "load_fn": load_fn,
        "load_outputs": all_outputs,
        "goto_analyze": goto_analyze,
        "goto_analyze_empty": goto_analyze_empty,
    }
