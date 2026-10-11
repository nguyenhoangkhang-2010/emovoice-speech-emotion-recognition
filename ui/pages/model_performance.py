# Mô hình & hiệu năng. Stitch: m_h_nh_hi_u_n_ng_ai. TOÀN BỘ số liệu đọc từ assets/metrics/*.json qua services.model_service (không hard-code số trong UI).
# Khác Stitch: Stitch tự đặt số HuBERT 74,10% / wav2vec 2.0 71,80% / SVM 54,80% / test 480 mẫu — không có trong báo cáo nên không dùng; mô hình chưa đo hiện "Chưa đo".
import gradio as gr

from services import model_service
from ui import i18n_vi as T
from ui import render

NAME = "models"
LABEL = T.NAV_MODELS
GROUP = "ml"
ADMIN_ONLY = False
EXTRA = False


def _active(metrics):
    return next(m for m in metrics["models"] if m["key"] == metrics["active_model"])


def _rf(metrics):
    return next((m for m in metrics["models"] if m["key"] == "random_forest"), None)


def _pending_names(metrics, field):
    return ", ".join(m["name"] for m in metrics["models"] if m.get("status") == "pending" and m.get(field) is None)


def _footers(metrics):
    active, rf = _active(metrics), _rf(metrics)
    delta = f"{active['accuracy'] - rf['accuracy']:+.2f}".replace(".", ",") if rf and rf.get("accuracy") is not None and active.get("accuracy") is not None else "—"
    pending = _pending_names(metrics, "latency_ms")
    pending_text = T.FOOT_PENDING_BASELINE.format(names=pending) if pending else ""
    return T.FOOT_DELTA_RF.format(delta=delta), f"{pending_text} {T.FOOT_LATENCY_NOTE}".strip(), pending_text


def _insights(metrics):
    active = _active(metrics)
    pt, ptot, ratio = active.get("params_trainable"), active.get("params_total"), active.get("trainable_ratio_pct")
    params_text = T.INSIGHT_PARAMS.format(trainable=f"{pt:,}".replace(",", "."), total=f"{ptot:,}".replace(",", "."), ratio=f"{ratio:.2f}".replace(".", ",")) if pt and ptot and ratio else "—"
    return [
        render.insight_html("graphic_eq", T.MODELS_INSIGHT_TITLES[0], T.INSIGHT_SAMPLING),
        render.insight_html("dataset", T.MODELS_INSIGHT_TITLES[1], params_text),
        render.insight_html("bolt", T.MODELS_INSIGHT_TITLES[2], T.MODELS_INSIGHT_QUANT),
    ]


def _cm_view(model_key):
    return render.confusion_matrix_html(model_service.load_confusion_matrix(model_key))


def load_fn(session):
    metrics = model_service.load_metrics()
    models, active_key = metrics["models"], metrics["active_model"]
    foot_acc, foot_lat, foot_size = _footers(metrics)
    return [
        render.model_hero_html(_active(metrics), metrics["dataset"]),
        render.comparison_bars_html(T.CHART_ACCURACY_TITLE, T.CHART_ACCURACY_UNIT, models, "accuracy", active_key, 2, foot_acc),
        render.comparison_bars_html(T.CHART_LATENCY_TITLE, T.CHART_LATENCY_UNIT, models, "latency_ms", active_key, 2, foot_lat),
        render.comparison_bars_html(T.CHART_SIZE_TITLE, T.CHART_SIZE_UNIT, models, "size_mib", active_key, 1, foot_size),
        f'<div class="ev ev-sub">{render.esc(T.COMPARISON_TABLE_SUB.format(n=metrics["test_samples"], dataset=metrics["dataset"]))}</div>',
        render.models_table_html(models, active_key),
        _cm_view(active_key),
        *_insights(metrics),
    ]


def build(session_state):
    gr.HTML(render.page_header_html(T.MODELS_EYEBROW, T.MODELS_TITLE, T.MODELS_SUB, render.tag_html(T.SOURCE_METRICS)), elem_classes=["ev-plain"])
    hero = gr.HTML("", elem_classes=["ev-plain"])
    with gr.Row(equal_height=True):
        chart_acc = gr.HTML("", elem_classes=["ev-plain"])
        chart_lat = gr.HTML("", elem_classes=["ev-plain"])
        chart_size = gr.HTML("", elem_classes=["ev-plain"])
    with gr.Column(elem_classes=["ev-card-col"]):
        gr.HTML(f'<div class="ev"><h2 class="ev-h3">{render.esc(T.COMPARISON_TABLE_TITLE)}</h2></div>', elem_classes=["ev-plain"])
        table_sub = gr.HTML("", elem_classes=["ev-plain"])
        table = gr.HTML("", elem_classes=["ev-plain"])
    with gr.Column(elem_classes=["ev-card-col"]):
        gr.HTML(
            f'<div class="ev"><h2 class="ev-h3">{render.esc(T.CM_TITLE)}</h2><p class="ev-sub">{render.esc(T.CM_SUB)}</p></div>',
            elem_classes=["ev-plain"],
        )
        cm_pick = gr.Dropdown(
            choices=[("DistilHuBERT + LoRA", "distilhubert_lora"), ("Random Forest", "random_forest")],
            value="distilhubert_lora", label=T.CM_PICK_MODEL, elem_classes=["ev-field", "ev-select"], scale=0,
        )
        cm = gr.HTML("", elem_classes=["ev-plain"])
    with gr.Row(equal_height=True):
        insights = [gr.HTML("", elem_classes=["ev-plain"]) for _ in range(3)]

    cm_pick.change(_cm_view, inputs=cm_pick, outputs=cm)
    return {
        "load_fn": load_fn,
        "load_outputs": [hero, chart_acc, chart_lat, chart_size, table_sub, table, cm, *insights],
    }
