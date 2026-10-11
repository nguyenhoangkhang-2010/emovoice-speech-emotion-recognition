# Phân tích mới (UC02, UC03, UC04, UC07) — 3 trạng thái bằng 3 Column bật/tắt + stepper 4 bước.
# Stitch: ph_n_t_ch_c_m_x_c_nh_p_m_thanh (nhập âm thanh) và k_t_qu_ph_n_t_ch_c_m_x_c_xai (kết quả); trạng thái "đang xử lý" chưa có Stitch riêng.
# Giai đoạn skeleton: dịch vụ chưa cài đặt nên nút phân tích hiển thị KẾT QUẢ MẪU CỨNG (có ghi chú), chưa gọi mô hình.
import time
from typing import List

import gradio as gr

from core.config import settings
from ml import xai
from services import audio_service, inference_service, preprocessing_service
from ui import i18n_vi as T
from ui import render
from ui.pages import guard_login

NAME = "analyze"
LABEL = T.NAV_ANALYZE
GROUP = "analysis"
ADMIN_ONLY = False
EXTRA = False

# --- dữ liệu mẫu cứng (thay bằng kết quả ml/ khi tích hợp UC04); thứ tự: neutral, calm, happy, sad, angry, fearful, disgust, surprised ---
SAMPLE_PROBS = [0.021, 0.002, 0.003, 0.010, 0.874, 0.010, 0.050, 0.030]
SAMPLE_REAL_DURATION = 2.4
SAMPLE_PEAK_RANGE = (1.4, 1.7)
_SAMPLE_SEGMENTS = [(0.0, 0.2, 0), (0.2, 0.5, 1), (0.5, 0.8, 3), (0.8, 1.1, 4), (1.1, 1.4, 2), (1.4, 1.7, 4), (1.7, 2.1, 3), (2.1, 2.4, 2), (2.4, 3.0, 0)]


def _sample_levels(n_cells: int = 30) -> List[int]:
    out = []
    for i in range(n_cells):
        t = (i + 0.5) * 3.0 / n_cells
        out.append(next(level for lo, hi, level in _SAMPLE_SEGMENTS if lo <= t < hi))
    return out


OUT_KEYS = ["stepper", "col_input", "col_processing", "col_result", "col_side", "processing", "hero", "bars", "heat", "banner", "diag"]


def _updates(stage: str, **values):
    base = {
        "stepper": gr.update(value=render.stepper_html(stage)),
        "col_input": gr.update(visible=stage == "input"),
        "col_processing": gr.update(visible=stage == "processing"),
        "col_result": gr.update(visible=stage == "result"),
        "col_side": gr.update(visible=stage != "result"),
    }
    base.update(values)
    return [base.get(key, gr.update()) for key in OUT_KEYS]


def _result_values(probs, levels, real_duration, peak_range, banner_html):
    return dict(
        hero=gr.update(value=render.emotion_hero_html(probs, peak_range, real_duration, settings.low_confidence_threshold)),
        bars=gr.update(value=render.emotion_bars_html(probs)),
        heat=gr.update(value=render.heatmap_html(levels, render.demo_waveform(voiced_ratio=real_duration / 3.0), real_duration)),
        banner=gr.update(value=banner_html),
    )


def run_analysis(upload_path, mic_path, source, session):
    guard_login(session)
    path = upload_path if source == "upload" else mic_path
    if not path:
        yield _updates("input", diag=gr.update(value=render.diagnostics_html(render.toast_html("warning", T.TOAST_NO_FILE_TITLE, T.TOAST_NO_FILE_TEXT, "UC02-W1"))))
        return
    try:
        audio_service.validate_upload(path)
    except NotImplementedError:
        pass  # TODO UC02: bỏ qua cho tới khi validate_upload được cài đặt
    except ValueError as exc:
        yield _updates("input", diag=gr.update(value=render.diagnostics_html(render.toast_html("error", T.TOAST_FORMAT_TITLE, str(exc), "UC02-E1"))))
        return

    yield _updates("processing", processing=gr.update(value=render.processing_html(1)))
    try:
        waveform = preprocessing_service.preprocess_audio(path)
        probs, attn = inference_service.run_inference(waveform)
        low = inference_service.is_low_confidence(probs)
        levels = xai.attention_to_levels(attn)
        banner = render.banner_html("warning", T.LOW_CONF_TITLE, T.LOW_CONF_TEXT.format(pct=int(settings.low_confidence_threshold * 100))) if low else ""
        # TODO UC04: real_duration và peak_range lấy từ preprocessing/xai; hiện dùng giá trị mặc định.
        yield _updates("result", **_result_values(probs, levels, 3.0, (0.0, 3.0), banner))
    except NotImplementedError:
        time.sleep(0.6)
        banner = render.banner_html("info", T.SAMPLE_DATA_TAG, T.SAMPLE_RESULT_NOTE)
        yield _updates("result", **_result_values(SAMPLE_PROBS, _sample_levels(), SAMPLE_REAL_DURATION, SAMPLE_PEAK_RANGE, banner))


def reset_view():
    return _updates("input", diag=gr.update(value=render.diagnostics_html()))


def build(session_state):
    source = gr.State("upload")
    stepper = gr.HTML(render.stepper_html("input"), elem_classes=["ev-plain"])
    with gr.Row(equal_height=False):
        with gr.Column(scale=8):
            # ---- Trạng thái 1: nhập âm thanh ----
            with gr.Column(visible=True) as col_input:
                with gr.Column(elem_classes=["ev-card-col"]):
                    with gr.Tabs(elem_classes=["ev-tabs"]):
                        with gr.Tab(T.TAB_UPLOAD) as tab_upload:
                            gr.HTML(f'<div class="ev ev-sub">{render.esc(T.UPLOAD_HINT.format(max_mb=settings.max_upload_mb))}</div>', elem_classes=["ev-plain"])
                            audio_up = gr.Audio(sources=["upload"], type="filepath", label=T.UPLOAD_TITLE, elem_classes=["ev-audio"])
                        with gr.Tab(T.TAB_RECORD) as tab_record:
                            audio_mic = gr.Audio(sources=["microphone"], type="filepath", label=T.TAB_RECORD, elem_classes=["ev-audio-mic"])
                    gr.HTML(render.preprocess_chips_html(), elem_classes=["ev-plain"])
                    analyze_btn = gr.Button(T.BTN_ANALYZE, variant="primary", elem_classes=["ev-btn-cta"])
                gr.HTML(
                    f'<div class="ev ev-card ev-tip"><span class="ev-icon ev-icon-primary ev-icon-lg">info</span><div><div class="ev-meta-strong">{render.esc(T.TIP_TITLE)}</div><p class="ev-sub">{render.esc(T.TIP_TEXT)}</p></div></div>',
                    elem_classes=["ev-plain"],
                )
            # ---- Trạng thái 2: đang xử lý (chưa có Stitch) ----
            with gr.Column(visible=False) as col_processing:
                processing = gr.HTML(render.processing_html(0), elem_classes=["ev-plain"])
            # ---- Trạng thái 3: kết quả ----
            with gr.Column(visible=False) as col_result:
                with gr.Row():
                    back_btn = gr.Button(T.BTN_ANALYZE_ANOTHER, elem_classes=["ev-btn-outline"], scale=0, min_width=200)
                    download_btn = gr.Button(T.BTN_DOWNLOAD_RESULT, elem_classes=["ev-btn-tint"], scale=0, min_width=180)
                with gr.Row(equal_height=True):
                    hero = gr.HTML("", elem_classes=["ev-plain"])
                    bars = gr.HTML("", elem_classes=["ev-plain"])
                heat = gr.HTML("", elem_classes=["ev-plain"])
                banner = gr.HTML("", elem_classes=["ev-plain"])
        with gr.Column(scale=4) as col_side:
            diag = gr.HTML(render.diagnostics_html(), elem_classes=["ev-plain"])
            gr.HTML(render.params_card_html("28,4 dB", "184 Hz", "0,082"), elem_classes=["ev-plain"])

    tab_upload.select(lambda: "upload", outputs=source)
    tab_record.select(lambda: "microphone", outputs=source)
    outputs = [stepper, col_input, col_processing, col_result, col_side, processing, hero, bars, heat, banner, diag]
    analyze_btn.click(run_analysis, inputs=[audio_up, audio_mic, source, session_state], outputs=outputs)
    back_btn.click(reset_view, outputs=outputs)
    # TODO UC04 (đề cương thang điểm mục 6): xuất ảnh kết quả từ XAI; hiện chỉ thông báo.
    download_btn.click(lambda: gr.Info("TODO UC04: tải ảnh kết quả chưa được cài đặt."))

    return {"stepper": stepper, "audio_upload": audio_up, "audio_mic": audio_mic, "analyze_btn": analyze_btn, "hero": hero, "bars": bars, "heat": heat}
