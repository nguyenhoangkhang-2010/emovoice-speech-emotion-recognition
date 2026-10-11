# Admin — Tổng quan (UC06). Stitch: qu_n_tr_h_th_ng_emovoice (một trang gộp tổng quan + người dùng + nhật ký; ở đây tách thành 3 trang).
# Nội dung chỉ được nạp qua load_fn SAU khi require_admin (guard_admin) — build() chỉ tạo khung rỗng.
# Mô hình đang dùng đọc từ assets/metrics; các số lượt dùng/tài khoản là dữ liệu mẫu cứng (admin_service.get_stats chưa cài đặt).
import gradio as gr

from services import admin_service, model_service, system_status_service
from ui import i18n_vi as T
from ui import render
from ui.components import charts
from ui.pages import guard_admin

NAME = "admin_overview"
LABEL = T.NAV_ADMIN_OVERVIEW
GROUP = "admin"
ADMIN_ONLY = True
EXTRA = False

# --- dữ liệu mẫu cứng (thay bằng admin_service.get_stats) ---
SAMPLE_STATS = {
    "analyses": 48290,
    "analyses_delta": "+12%",
    "accounts": 1248,
    "online": 94,
    "daily_labels": ["T2", "T3", "T4", "T5", "T6", "T7", "CN"],
    "daily_values": [4810, 5620, 5140, 6890, 7420, 6180, 4120],
    # Stitch dùng nhãn ngoài 8 lớp (Khinh bỉ, Hào hứng); ở đây quy về 8 lớp của mô hình.
    "distribution": {"neutral": 28, "happy": 22, "sad": 16, "angry": 12, "surprised": 8, "fearful": 6, "disgust": 5, "calm": 3},
}


def _kpis():
    metrics = model_service.load_metrics()
    active = next(m for m in metrics["models"] if m["key"] == metrics["active_model"])
    s = SAMPLE_STATS
    return [
        render.kpi_card_html(T.KPI_ANALYSES, "bar_chart", f"{s['analyses']:,}", f'<span class="ev-tone-up">{s["analyses_delta"]}</span> {render.tag_html(T.SAMPLE_DATA_TAG)}'),
        render.kpi_card_html(T.KPI_ACCOUNTS, "group", f"{s['accounts']:,}", f'<span class="ev-dot ev-dot-teal ev-dot-sm"></span>{s["online"]} trực tuyến {render.tag_html(T.SAMPLE_DATA_TAG)}'),
        render.kpi_card_html(
            T.KPI_ACTIVE_MODEL, "memory", f'<span class="ev-kpi-value-sm">{render.esc(active["name"])}</span>',
            f'Độ trễ: {active["latency_ms"]:.2f} ms/mẫu | Accuracy {active["accuracy"]:.2f}%',
        ),
        render.kpi_card_html(T.KPI_SERVICE, "verified", f'<span class="ev-kpi-value-sm">{render.esc(T.KPI_SERVICE_OK)}</span>', render.tag_html(T.SAMPLE_DATA_TAG)),
    ]


def _status_rows():
    # TODO UC06: thay bằng system_status_service.get_system_status (kiểm tra DB/kho tệp/mô hình thật).
    names = T.STATUS_NAMES
    metrics = model_service.load_metrics()
    active = next(m for m in metrics["models"] if m["key"] == metrics["active_model"])
    return [
        render.status_row_html(names[0][0], names[0][1], "ok", T.STATUS_OK, "—"),
        render.status_row_html(names[1][0], names[1][1], "ok", T.STATUS_OK, f'{active["latency_ms"]:.2f} ms/mẫu', icon="speed"),
        render.status_row_html(names[2][0], names[2][1], "ok", T.STATUS_OK, "—", icon="sync_saved_locally"),
    ]


def load_fn(session):
    guard_admin(session)
    try:
        admin_service.get_stats(session)
        system_status_service.get_system_status(session)
    except NotImplementedError:
        pass  # skeleton: dùng SAMPLE_STATS
    s = SAMPLE_STATS
    return [
        *_kpis(),
        charts.daily_bar_figure(s["daily_labels"], s["daily_values"]),
        charts.emotion_donut_figure(s["distribution"]),
        *_status_rows(),
    ]


def build(session_state):
    gr.HTML(render.page_header_html(T.ADMIN_OVERVIEW_EYEBROW, T.ADMIN_OVERVIEW_TITLE, "", ""), elem_classes=["ev-plain"])
    with gr.Row(equal_height=True):
        kpis = [gr.HTML("", elem_classes=["ev-plain"]) for _ in range(4)]
    with gr.Row(equal_height=True):
        with gr.Column(scale=7, elem_classes=["ev-card-col"]):
            gr.HTML(f'<div class="ev"><h3 class="ev-h3">{render.esc(T.CHART_DAILY_TITLE)}</h3><p class="ev-meta">{render.esc(T.CHART_DAILY_SUB)}</p></div>', elem_classes=["ev-plain"])
            daily = gr.Plot(show_label=False, container=False)
        with gr.Column(scale=5, elem_classes=["ev-card-col"]):
            gr.HTML(f'<div class="ev"><h3 class="ev-h3">{render.esc(T.CHART_DIST_TITLE)}</h3><p class="ev-meta">{render.esc(T.CHART_DIST_SUB)}</p></div>', elem_classes=["ev-plain"])
            donut = gr.Plot(show_label=False, container=False)
    with gr.Column(elem_classes=["ev-card-col"]):
        gr.HTML(f'<div class="ev"><h3 class="ev-h3">{render.esc(T.STATUS_TITLE)}</h3><p class="ev-meta">{render.esc(T.STATUS_SUB)}</p></div>', elem_classes=["ev-plain"])
        with gr.Row(equal_height=True):
            status = [gr.HTML("", elem_classes=["ev-plain"]) for _ in range(3)]
    return {"load_fn": load_fn, "load_outputs": [*kpis, daily, donut, *status]}
