# Admin — Tổng quan (UC06). Stitch: qu_n_tr_h_th_ng_emovoice (một trang gộp tổng quan + người dùng + nhật ký; ở đây tách thành 3 trang).
# Nội dung chỉ được nạp qua load_fn SAU khi require_admin (guard_admin) — build() chỉ tạo khung rỗng.
# Số liệu THẬT: lượt phân tích, tài khoản, phân bố cảm xúc, lượt theo ngày từ admin_service.get_stats; mô hình đang dùng từ bảng models.
# Hàng "Trạng thái dịch vụ" vẫn là kiểm tra sơ bộ, sẽ thay bằng system_status_service ở nhánh feat/status.
import logging

import gradio as gr
from sqlalchemy.exc import SQLAlchemyError

from db.session import engine
from services import admin_service, model_service
from ui import i18n_vi as T
from ui import render
from ui.components import charts
from ui.pages import guard_admin

logger = logging.getLogger(__name__)

NAME = "admin_overview"
LABEL = T.NAV_ADMIN_OVERVIEW
GROUP = "admin"
ADMIN_ONLY = True
EXTRA = False

DB_LABELS = {"postgresql": "PostgreSQL", "sqlite": "SQLite", "mysql": "MySQL"}

EMPTY_STATS = {
    "analyses": 0, "analyses_week": 0, "analyses_prev_week": 0, "accounts": 0, "accounts_total": 0, "accounts_locked": 0,
    "daily_labels": ["—"] * 7, "daily_values": [0] * 7, "distribution": {},
}


def _active():
    """Mô hình đang dùng từ bảng models; None nếu chưa đăng ký mô hình nào hoặc chưa đọc được CSDL."""
    try:
        return model_service.active_model()
    except model_service.RegistryUnavailable:
        return None


def _delta_html(stats) -> str:
    """So sánh 7 ngày gần nhất với 7 ngày trước đó; chưa có kỳ trước để so thì chỉ nêu số lượt."""
    week, prev = stats["analyses_week"], stats["analyses_prev_week"]
    if prev:
        change = (week - prev) / prev * 100
        tone = ' class="ev-tone-up"' if change >= 0 else ""
        return f"<span{tone}>{change:+.0f}%</span> {render.esc(T.KPI_VS_LAST_WEEK)}"
    return render.esc(T.KPI_WEEK_COUNT.format(n=week))


def _kpis(stats):
    active = _active()
    return [
        render.kpi_card_html(T.KPI_ANALYSES, "bar_chart", f"{stats['analyses']:,}", _delta_html(stats)),
        render.kpi_card_html(
            T.KPI_ACCOUNTS, "group", f"{stats['accounts']:,}",
            f'<span class="ev-dot ev-dot-teal ev-dot-sm"></span>{render.esc(T.KPI_ACCOUNTS_SUB.format(total=stats["accounts_total"], locked=stats["accounts_locked"]))}',
        ),
        render.kpi_card_html(
            T.KPI_ACTIVE_MODEL, "memory", f'<span class="ev-kpi-value-sm">{render.esc(active["name"] if active else "—")}</span>',
            f'Độ trễ: {active["latency_ms"]:.2f} ms/mẫu ({active["latency_device"]}) | Accuracy {active["accuracy"]:.2f}%' if active else T.MODELS_EMPTY_TITLE,
        ),
        render.kpi_card_html(T.KPI_SERVICE, "verified", f'<span class="ev-kpi-value-sm">{render.esc(T.KPI_SERVICE_OK)}</span>', render.tag_html(T.SAMPLE_DATA_TAG)),
    ]


def _distribution(stats) -> str:
    if not sum(stats["distribution"].values()):
        return render.empty_state_html("graphic_eq", T.ADMIN_NO_ANALYSES_TITLE, T.ADMIN_NO_ANALYSES_TEXT)
    return render.distribution_html(stats["distribution"])


def _status_rows():
    # TODO nhánh feat/status: thay bằng system_status_service.get_system_status (kiểm tra DB/kho tệp/mô hình thật).
    names = T.STATUS_NAMES
    active = _active()
    model_row = (
        render.status_row_html(names[1][0], names[1][1].format(model=active["name"]), "ok", T.STATUS_OK, f'{active["latency_ms"]:.2f} ms/mẫu ({active["latency_device"]})', icon="speed")
        if active
        else render.status_row_html(names[1][0], T.MODELS_EMPTY_TITLE, "warn", T.STATUS_NOT_READY, "—", icon="speed")
    )
    return [
        render.status_row_html(names[0][0], names[0][1], "ok", T.STATUS_OK, "—"),
        model_row,
        render.status_row_html(names[2][0], names[2][1].format(database=DB_LABELS.get(engine.dialect.name, engine.dialect.name)), "ok", T.STATUS_OK, "—", icon="sync_saved_locally"),
    ]


def load_fn(session):
    guard_admin(session)
    try:
        stats = admin_service.get_stats(session)
    except SQLAlchemyError:
        logger.exception("Không đọc được số liệu thống kê")
        gr.Warning(T.MSG_DB_ERROR)
        stats = EMPTY_STATS
    return [
        *_kpis(stats),
        charts.daily_bar_figure(stats["daily_labels"], stats["daily_values"]),
        _distribution(stats),
        *_status_rows(),
    ]


def build(session_state):
    gr.HTML(render.page_header_html(T.ADMIN_OVERVIEW_EYEBROW, T.ADMIN_OVERVIEW_TITLE, "", ""), elem_classes=["ev-plain"])
    with gr.Row(equal_height=True, elem_classes=["ev-kpi-strip"]):
        kpis = [gr.HTML("", elem_classes=["ev-plain"]) for _ in range(4)]
    with gr.Row(equal_height=True, elem_classes=["ev-section"]):
        with gr.Column(scale=7):
            gr.HTML(f'<div class="ev"><h3 class="ev-h3">{render.esc(T.CHART_DAILY_TITLE)}</h3><p class="ev-meta">{render.esc(T.CHART_DAILY_SUB)}</p></div>', elem_classes=["ev-plain"])
            daily = gr.Plot(show_label=False, container=False)
        with gr.Column(scale=5):
            gr.HTML(f'<div class="ev"><h3 class="ev-h3">{render.esc(T.CHART_DIST_TITLE)}</h3><p class="ev-meta">{render.esc(T.CHART_DIST_SUB)}</p></div>', elem_classes=["ev-plain"])
            donut = gr.HTML("", elem_classes=["ev-plain"])
    with gr.Column(elem_classes=["ev-section"]):
        gr.HTML(f'<div class="ev"><h3 class="ev-h3">{render.esc(T.STATUS_TITLE)}</h3><p class="ev-meta">{render.esc(T.STATUS_SUB)}</p></div>', elem_classes=["ev-plain"])
        with gr.Row(equal_height=True, elem_classes=["ev-status-list"]):
            status = [gr.HTML("", elem_classes=["ev-plain"]) for _ in range(3)]
    return {"load_fn": load_fn, "load_outputs": [*kpis, daily, donut, *status]}
