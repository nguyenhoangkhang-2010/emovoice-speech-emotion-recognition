# Mô hình & hiệu năng (chỉ Admin xem). Stitch: m_h_nh_hi_u_n_ng_ai. TOÀN BỘ số liệu đọc từ bảng models qua services.model_service
# (được ghi bởi `python -m ml.register_model` sau khi đánh giá mô hình thật); không hard-code số trong UI.
# Chưa đăng ký mô hình nào hoặc chưa kết nối được CSDL thì trang hiện hướng dẫn thay vì số liệu.
import gradio as gr

from services import model_service
from ui import i18n_vi as T
from ui import render
from ui.pages import guard_admin

NAME = "models"
LABEL = T.NAV_MODELS
GROUP = "admin"
ADMIN_ONLY = True
EXTRA = False


def _active(metrics):
    return next((m for m in metrics["models"] if m["key"] == metrics["active_model"]), metrics["models"][0])


def _footers(metrics):
    """Chú thích dưới ba biểu đồ: chênh lệch accuracy với mô hình tốt nhất còn lại; độ trễ chỉ so được khi cùng thiết bị."""
    active = _active(metrics)
    others = [m for m in metrics["models"] if m["key"] != active["key"] and m.get("accuracy") is not None]
    best = max(others, key=lambda m: m["accuracy"], default=None)
    delta = T.FOOT_DELTA_OTHER.format(name=best["name"], delta=f"{active['accuracy'] - best['accuracy']:+.2f}".replace(".", ",")) if best and active.get("accuracy") is not None else ""
    return delta, T.FOOT_LATENCY_NOTE, ""


def _insights(metrics):
    active = _active(metrics)
    pt, ptot, ratio = active.get("params_trainable"), active.get("params_total"), active.get("trainable_ratio_pct")
    params_text = T.INSIGHT_PARAMS.format(trainable=f"{pt:,}".replace(",", "."), total=f"{ptot:,}".replace(",", "."), ratio=f"{ratio:.2f}".replace(".", ",")) if pt and ptot and ratio else "—"
    return [
        render.insight_html("graphic_eq", T.MODELS_INSIGHT_TITLES[0], T.INSIGHT_SAMPLING),
        render.insight_html("dataset", T.MODELS_INSIGHT_TITLES[1], params_text),
        render.insight_html("bolt", T.MODELS_INSIGHT_TITLES[2], T.MODELS_INSIGHT_QUANT),
    ]


def _cm_view(session, model_key):
    guard_admin(session)
    return render.confusion_matrix_html(model_service.load_confusion_matrix(model_key) if model_key else None)


def _empty_outputs(message_html):
    """[empty, body(ẩn), hero, 3 biểu đồ, table_sub, table, cm, 3 insight, cm_pick]"""
    return [message_html, gr.update(visible=False), "", "", "", "", "", "", "", "", "", "", gr.update(choices=[], value=None)]


def load_fn(session):
    guard_admin(session)
    try:
        metrics = model_service.load_metrics()
        options = model_service.confusion_matrix_options()
    except model_service.RegistryUnavailable as exc:
        return _empty_outputs(render.empty_state_html("database", T.MODELS_UNAVAILABLE_TITLE, str(exc)))
    if not metrics["models"]:
        return _empty_outputs(render.empty_state_html("model_training", T.MODELS_EMPTY_TITLE, T.MODELS_EMPTY_TEXT))
    models, active_key = metrics["models"], metrics["active_model"]
    foot_acc, foot_lat, foot_size = _footers(metrics)
    cm_key = active_key if any(key == active_key for _, key in options) else (options[0][1] if options else None)
    return [
        "",
        gr.update(visible=True),
        render.model_hero_html(_active(metrics), metrics["dataset"]),
        render.comparison_bars_html(T.CHART_ACCURACY_TITLE, T.CHART_ACCURACY_UNIT, models, "accuracy", active_key, 2, foot_acc),
        render.comparison_bars_html(T.CHART_LATENCY_TITLE, T.CHART_LATENCY_UNIT, models, "latency_ms", active_key, 2, foot_lat),
        render.comparison_bars_html(T.CHART_SIZE_TITLE, T.CHART_SIZE_UNIT, models, "size_mib", active_key, 1, foot_size),
        f'<div class="ev ev-sub">{render.esc(T.COMPARISON_TABLE_SUB.format(n=metrics["test_samples"], dataset=metrics["dataset"]))}</div>',
        render.models_table_html(models, active_key),
        render.confusion_matrix_html(model_service.load_confusion_matrix(cm_key) if cm_key else None),
        *_insights(metrics),
        gr.update(choices=options, value=cm_key),
    ]


def build(session_state):
    gr.HTML(render.page_header_html(T.MODELS_EYEBROW, T.MODELS_TITLE, T.MODELS_SUB, render.tag_html(T.SOURCE_METRICS)), elem_classes=["ev-plain"])
    empty = gr.HTML("", elem_classes=["ev-plain"])
    with gr.Column(visible=False, elem_classes=["ev-models-body"]) as body:
        hero = gr.HTML("", elem_classes=["ev-plain"])
        with gr.Row(equal_height=True, elem_classes=["ev-section"]):
            chart_acc = gr.HTML("", elem_classes=["ev-plain"])
            chart_lat = gr.HTML("", elem_classes=["ev-plain"])
            chart_size = gr.HTML("", elem_classes=["ev-plain"])
        with gr.Column(elem_classes=["ev-section"]):
            gr.HTML(f'<div class="ev"><h2 class="ev-h3">{render.esc(T.COMPARISON_TABLE_TITLE)}</h2></div>', elem_classes=["ev-plain"])
            table_sub = gr.HTML("", elem_classes=["ev-plain"])
            table = gr.HTML("", elem_classes=["ev-plain"])
        with gr.Column(elem_classes=["ev-section"]):
            gr.HTML(
                f'<div class="ev"><h2 class="ev-h3">{render.esc(T.CM_TITLE)}</h2><p class="ev-sub">{render.esc(T.CM_SUB)}</p></div>',
                elem_classes=["ev-plain"],
            )
            cm_pick = gr.Dropdown(choices=[], label=T.CM_PICK_MODEL, elem_classes=["ev-field", "ev-select", "ev-field-narrow"], scale=0)
            cm = gr.HTML("", elem_classes=["ev-plain"])
        with gr.Row(equal_height=True, elem_classes=["ev-section"]):
            insights = [gr.HTML("", elem_classes=["ev-plain"]) for _ in range(3)]

    cm_pick.change(_cm_view, inputs=[session_state, cm_pick], outputs=cm)
    return {
        "load_fn": load_fn,
        "load_outputs": [empty, body, hero, chart_acc, chart_lat, chart_size, table_sub, table, cm, *insights, cm_pick],
    }
