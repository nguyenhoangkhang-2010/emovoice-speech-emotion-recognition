# Admin — Quản lý mô hình AI (đề cương: "Quản trị viên: quản lý dữ liệu và mô hình"): xem chỉ số, chọn mô hình đang dùng.
# CHƯA có khung Stitch — dựng theo style Stitch; chỉ hiện trong sidebar khi ENABLE_ADMIN_EXTRA_PAGES=1. Mọi handler gọi guard_admin.
import gradio as gr

from services import model_service
from ui import i18n_vi as T
from ui import render
from ui.pages import guard_admin

NAME = "admin_models"
LABEL = T.NAV_ADMIN_MODELS
GROUP = "admin"
ADMIN_ONLY = True
EXTRA = True


def _choices(metrics):
    return [(m["name"], m["key"]) for m in metrics["models"] if m.get("status") != "pending"]


def load_fn(session):
    guard_admin(session)
    metrics = model_service.load_metrics()
    return [render.models_table_html(metrics["models"], metrics["active_model"]), gr.update(choices=_choices(metrics), value=metrics["active_model"])]


def build(session_state):
    gr.HTML(render.page_header_html(T.ADMIN_MODELS_EYEBROW, T.ADMIN_MODELS_TITLE, T.ADMIN_MODELS_SUB, ""), elem_classes=["ev-plain"])
    table = gr.HTML("", elem_classes=["ev-plain"])
    with gr.Row():
        pick = gr.Dropdown(label=T.CM_PICK_MODEL, choices=[], elem_classes=["ev-field", "ev-select"], scale=3)
        apply_btn = gr.Button(T.BTN_SET_ACTIVE_MODEL, elem_classes=["ev-btn-cta", "ev-btn-sm"], scale=0, min_width=240)
    message = gr.HTML("", elem_classes=["ev-plain"])

    def on_apply(session, model_key):
        guard_admin(session)
        try:
            model_service.set_active_model(session, model_key)  # TODO: truyền model_id từ bảng models khi có DB
        except NotImplementedError as exc:
            return render.message_html(T.MSG_ADMIN_NOT_IMPLEMENTED.format(detail=exc), "info")
        return render.message_html(T.MSG_DONE, "success")

    apply_btn.click(on_apply, inputs=[session_state, pick], outputs=message)
    return {"load_fn": load_fn, "load_outputs": [table, pick]}
