# Phân tích mới (UC02, UC03, UC04, UC07) — 3 trạng thái bằng 3 Column bật/tắt + stepper 4 bước.
# Stitch: ph_n_t_ch_c_m_x_c_nh_p_m_thanh (nhập âm thanh) và k_t_qu_ph_n_t_ch_c_m_x_c_xai (kết quả); trạng thái "đang xử lý" chưa có Stitch riêng.
# Kết quả là THẬT: tiền xử lý -> mô hình đang dùng (bảng models) -> xác suất 8 lớp + attention -> ảnh XAI.
# Tài khoản thật được lưu tệp + đặc trưng + kết quả vào CSDL (cho lịch sử UC05); phiên "Vào thử" không lưu.
import logging
import os
import time

import gradio as gr

from core.config import settings
from ml import xai
from ml.config import EMOTION_NAMES
from services import audio_service, audit_service, baseline_service, inference_service, preprocessing_service, xai_service
from ui import i18n_vi as T
from ui import render
from ui.pages import guard_login

logger = logging.getLogger(__name__)

NAME = "analyze"
LABEL = T.NAV_ANALYZE
GROUP = "analysis"
ADMIN_ONLY = False
EXTRA = False

OUT_KEYS = ["stepper", "col_input", "col_processing", "col_result", "col_side", "processing", "hero", "bars", "heat", "banner", "diag", "params", "download", "mel_title", "mel", "baseline_col", "baseline"]


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


def _result_values(probs, levels, envelope, real_duration, peak_range, banner_html):
    return dict(
        hero=gr.update(value=render.emotion_hero_html(probs, peak_range, real_duration, settings.low_confidence_threshold)),
        bars=gr.update(value=render.emotion_bars_html(probs)),
        heat=gr.update(value=render.heatmap_html(levels, envelope, real_duration)),
        banner=gr.update(value=banner_html),
    )


def _toast(level, title, text, code):
    return gr.update(value=render.diagnostics_html(render.toast_html(level, title, text, code)))


def run_analysis(upload_path, mic_path, source, session, compare_rf=False):
    user = guard_login(session)
    started = time.perf_counter()
    path = upload_path if source == "upload" else mic_path
    if not path:
        yield _updates("input", diag=_toast("warning", T.TOAST_NO_FILE_TITLE, T.TOAST_NO_FILE_TEXT, "UC02-W1"))
        return
    try:
        audio_service.validate_upload(path)
    except ValueError as exc:
        audit_service.log("WARNING", "audio", f"Tệp bị từ chối ({os.path.basename(path)}): {exc}", user)
        yield _updates("input", diag=_toast("error", T.TOAST_FORMAT_TITLE, str(exc), "UC02-E1"))
        return

    yield _updates("processing", processing=gr.update(value=render.processing_html(1)))
    try:
        waveform, real_duration = preprocessing_service.preprocess_with_duration(path)
    except Exception:  # librosa/soundfile báo nhiều loại lỗi khác nhau khi không giải mã được tệp
        audit_service.log("ERROR", "preprocess", f"Không đọc được âm thanh ({os.path.basename(path)})", user)
        yield _updates("input", diag=_toast("error", T.TOAST_DECODE_TITLE, T.TOAST_DECODE_TEXT, "UC02-E2"))
        return
    yield _updates("processing", processing=gr.update(value=render.processing_html(3)))
    try:
        probs, attn = inference_service.run_inference(waveform)
    except inference_service.ModelNotReady as exc:
        audit_service.log("ERROR", "inference", f"Không phân tích được ({os.path.basename(path)}): {exc}", user)
        yield _updates("input", diag=_toast("error", T.TOAST_MODEL_TITLE, str(exc), "UC04-E1"))
        return
    yield _updates("processing", processing=gr.update(value=render.processing_html(4)))
    baseline_html = _baseline_section(path, probs, user) if compare_rf else ""
    levels = xai.attention_to_levels(attn)
    low = inference_service.is_low_confidence(probs)
    banner = render.banner_html("warning", T.LOW_CONF_TITLE, T.LOW_CONF_TEXT.format(pct=int(settings.low_confidence_threshold * 100))) if low else ""
    try:
        image_path = xai_service.build_waveform_heatmap(waveform, attn, real_duration)
    except Exception:
        logger.exception("Không vẽ được ảnh XAI")
        audit_service.log("WARNING", "xai", f"Không vẽ được ảnh XAI ({os.path.basename(path)})", user)
        image_path = None  # không vẽ được ảnh thì vẫn hiện kết quả trên giao diện
    try:
        mel_path = xai_service.build_mel_attention(waveform, attn, real_duration)
    except Exception:
        logger.exception("Không vẽ được ảnh Mel")
        audit_service.log("WARNING", "xai", f"Không vẽ được ảnh Mel ({os.path.basename(path)})", user)
        mel_path = None
    if user.is_demo:
        banner += render.banner_html("info", T.SAVE_DEMO_TITLE, T.SAVE_DEMO_TEXT)
    else:
        try:
            _persist(user, path, waveform, real_duration, probs, image_path, mel_path)
        except Exception:
            logger.exception("Không lưu được lịch sử phân tích")
            audit_service.log("ERROR", "audio", f"Không lưu được lịch sử cho {os.path.basename(path)}", user)
            banner += render.banner_html("warning", T.SAVE_FAILED_TITLE, T.SAVE_FAILED_TEXT)
    _log_analysis_done(user, path, probs, started)
    yield _updates(
        "result",
        download=gr.update(value=image_path, interactive=image_path is not None),
        mel_title=gr.update(value=render.mel_title_html() if mel_path else ""),
        mel=gr.update(value=mel_path, visible=mel_path is not None),
        baseline_col=gr.update(visible=bool(baseline_html)),
        baseline=gr.update(value=baseline_html),
        **_result_values(probs, levels, xai.waveform_envelope(waveform), real_duration, xai.peak_range(levels), banner),
    )


def _log_analysis_done(user, path, probs, started) -> None:
    """Một dòng nhật ký cho mỗi lượt phân tích hoàn tất: tên tệp, nhãn + độ tin cậy, mô hình, thời gian suy luận và tổng thời gian."""
    top = max(range(len(probs)), key=lambda i: probs[i])
    model_ms = inference_service.last_latency_ms()
    detail = f"{inference_service.last_model_name() or '?'}, suy luận {model_ms:.0f} ms, tổng {time.perf_counter() - started:.1f} s" if model_ms is not None else f"tổng {time.perf_counter() - started:.1f} s"
    suffix = " [phiên thử, không lưu]" if user.is_demo else ""
    audit_service.log("INFO", "inference", f"Phân tích {os.path.basename(path)} → {T.EMOTION_VI[EMOTION_NAMES[top]]} {float(probs[top]) * 100:.1f}% ({detail}){suffix}", user)


def _baseline_section(path, probs, user=None) -> str:
    """HTML so sánh với baseline Random Forest; lỗi của baseline chỉ hiện thành thông báo, không làm hỏng kết quả của mô hình chính."""
    try:
        return render.baseline_compare_html(inference_service.last_model_name(), probs, baseline_service.run_random_forest(path))
    except baseline_service.BaselineNotReady as exc:
        audit_service.log("WARNING", "baseline", f"Không so sánh được với Random Forest: {exc}", user)
        return render.baseline_unavailable_html(str(exc))
    except Exception:
        logger.exception("Không so sánh được với baseline")
        audit_service.log("ERROR", "baseline", "Baseline Random Forest lỗi bất ngờ", user)
        return render.baseline_unavailable_html(baseline_service.MSG_LOAD_FAILED)


def _persist(user, path, waveform, real_duration, probs, image_path, mel_path=None):
    """Lưu tệp, đặc trưng và kết quả của một lượt phân tích (cho lịch sử, UC05)."""
    audio = audio_service.save_upload(user, path)
    if audio is None:
        return
    preprocessing_service.save_audio_features(audio["audio_id"], waveform, real_duration, mel_path)
    inference_service.save_prediction(user, audio["audio_id"], probs, image_path)


def reset_view():
    return _updates("input", diag=gr.update(value=render.diagnostics_html()))


def _duration(path: str):
    try:
        import soundfile as sf

        return float(sf.info(path).duration)
    except Exception:
        pass
    try:
        import wave

        with wave.open(path) as w:
            return w.getnframes() / w.getframerate()
    except Exception:
        return None  # ví dụ MP3 khi chưa cài soundfile: không hiện thời lượng


def show_params(path):
    """SNR / F0 / ZCR ước lượng từ chính tệp đã chọn; chưa chọn hoặc không đọc được thì hiện dấu gạch."""
    values = {}
    if path:
        try:
            values = preprocessing_service.compute_input_diagnostics(path)
        except Exception:
            values = {}

    def fmt(key, pattern):
        return pattern.format(values[key]).replace(".", ",") if values.get(key) is not None else "—"

    return render.params_card_html(fmt("snr_db", "{:.1f} dB"), fmt("f0_hz", "{:.0f} Hz"), fmt("zcr", "{:.3f}"))


def show_file_chip(path):
    if not path:
        return ""
    try:
        return render.file_chip_html(os.path.basename(path), os.path.getsize(path), _duration(path))
    except OSError:
        return ""


def build(session_state):
    source = gr.State("upload")
    stepper = gr.HTML(render.stepper_html("input"), elem_classes=["ev-plain"])
    with gr.Row(equal_height=False):
        with gr.Column(scale=8):
            # ---- Trạng thái 1: nhập âm thanh ----
            with gr.Column(visible=True) as col_input:
                with gr.Column(elem_classes=["ev-work"]):
                    with gr.Tabs(elem_classes=["ev-tabs"]):
                        with gr.Tab(T.TAB_UPLOAD) as tab_upload:
                            audio_up = gr.Audio(
                                sources=["upload"], type="filepath", label=T.UPLOAD_TITLE, elem_classes=["ev-audio", "ev-audio-drop"],
                                waveform_options=gr.WaveformOptions(waveform_color="#B9B29E", waveform_progress_color="#14130F"),
                            )
                            file_chip = gr.HTML("", elem_classes=["ev-plain"])
                        with gr.Tab(T.TAB_RECORD) as tab_record:
                            audio_mic = gr.Audio(
                                sources=["microphone"], type="filepath", label=T.TAB_RECORD, elem_classes=["ev-audio", "ev-audio-mic"],
                                waveform_options=gr.WaveformOptions(waveform_color="#B9B29E", waveform_progress_color="#14130F"),
                            )
                    gr.HTML(render.preprocess_chips_html(), elem_classes=["ev-plain"])
                    compare_rf = gr.Checkbox(label=T.COMPARE_RF_LABEL, info=T.COMPARE_RF_INFO, value=True, elem_classes=["ev-compare-check"])
                    analyze_btn = gr.Button(T.BTN_ANALYZE, variant="primary", elem_classes=["ev-btn-cta"])
                gr.HTML(
                    f'<div class="ev ev-tip"><span class="ev-icon ev-icon-primary ev-icon-lg">info</span><div><div class="ev-meta-strong">{render.esc(T.TIP_TITLE)}</div><p class="ev-sub">{render.esc(T.TIP_TEXT)}</p></div></div>',
                    elem_classes=["ev-plain"],
                )
            # ---- Trạng thái 2: đang xử lý (chưa có Stitch) ----
            with gr.Column(visible=False) as col_processing:
                processing = gr.HTML(render.processing_html(0), elem_classes=["ev-plain"])
            # ---- Trạng thái 3: kết quả ----
            with gr.Column(visible=False, elem_classes=["ev-result"]) as col_result:
                with gr.Row():
                    back_btn = gr.Button(T.BTN_ANALYZE_ANOTHER, elem_classes=["ev-btn-outline"], scale=0, min_width=200)
                    download_btn = gr.DownloadButton(T.BTN_DOWNLOAD_RESULT, elem_classes=["ev-btn-tint"], scale=0, min_width=180)
                with gr.Row(equal_height=True, elem_classes=["ev-result-row"]):
                    hero = gr.HTML("", elem_classes=["ev-plain"])
                    bars = gr.HTML("", elem_classes=["ev-plain"])
                with gr.Column(visible=False, elem_classes=["ev-section"]) as baseline_col:  # mục so sánh baseline, chỉ hiện khi người dùng chọn
                    baseline = gr.HTML("", elem_classes=["ev-plain"])
                heat = gr.HTML("", elem_classes=["ev-plain"])
                with gr.Column(elem_classes=["ev-section"]):  # mục có đánh số (03 ——) như các mục khác của trang kết quả
                    mel_title = gr.HTML("", elem_classes=["ev-plain"])
                    mel = gr.Image(show_label=False, container=False, interactive=False, type="filepath", visible=False, buttons=[], elem_classes=["ev-xai-image"])
                banner = gr.HTML("", elem_classes=["ev-plain"])
        with gr.Column(scale=4, elem_classes=["ev-aside"]) as col_side:
            diag = gr.HTML(render.diagnostics_html(), elem_classes=["ev-plain"])
            params = gr.HTML(show_params(None), elem_classes=["ev-plain"])

    audio_up.change(show_file_chip, inputs=audio_up, outputs=file_chip)
    audio_up.change(show_params, inputs=audio_up, outputs=params)
    audio_mic.change(show_params, inputs=audio_mic, outputs=params)
    tab_upload.select(lambda: "upload", outputs=source)
    tab_record.select(lambda: "microphone", outputs=source)
    outputs = [stepper, col_input, col_processing, col_result, col_side, processing, hero, bars, heat, banner, diag, params, download_btn, mel_title, mel, baseline_col, baseline]
    analyze_btn.click(run_analysis, inputs=[audio_up, audio_mic, source, session_state, compare_rf], outputs=outputs)
    back_btn.click(reset_view, outputs=outputs)

    return {"stepper": stepper, "audio_upload": audio_up, "audio_mic": audio_mic, "analyze_btn": analyze_btn, "hero": hero, "bars": bars, "heat": heat}
