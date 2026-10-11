# Dựng HTML cho các khối phức tạp từ ui/templates (gr.HTML). Không import gradio để kiểm thử độc lập được.
# Quy ước template: {{key}} được escape; khóa kết thúc bằng _html được chèn nguyên văn. Chuỗi hiển thị lấy từ ui/i18n_vi.py.
import html
import math
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from ml.config import EMOTION_NAMES
from ui import i18n_vi as T

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

EMOTION_COLORS: Dict[str, str] = {
    "neutral": "#8C9BB8",
    "calm": "#5BB5C6",
    "happy": "#F2C14E",
    "sad": "#6A88D7",
    "angry": "#E5675B",
    "fearful": "#9A82C9",
    "disgust": "#84B26B",
    "surprised": "#F29A52",
}
EMOTION_ICONS: Dict[str, str] = {
    "neutral": "sentiment_neutral",
    "calm": "self_improvement",
    "happy": "sentiment_very_satisfied",
    "sad": "sentiment_dissatisfied",
    "angry": "sentiment_very_dissatisfied",
    "fearful": "sentiment_stressed",
    "disgust": "mood_bad",
    "surprised": "sentiment_excited",
}
HEAT_LEVELS: List[str] = ["#E8EDFC", "#C5D1F7", "#9DB1F0", "#6F89E6", "#4361D8"]


# ---------- tiện ích chung ----------
@lru_cache(maxsize=None)
def _read_template(name: str) -> str:
    return (TEMPLATE_DIR / f"{name}.html").read_text(encoding="utf-8")


_PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")


def render(template: str, /, **ctx) -> str:
    def _sub(match: "re.Match") -> str:
        key = match.group(1)
        value = ctx.get(key, "")
        return str(value) if key.endswith("_html") else html.escape(str(value))

    return _PLACEHOLDER.sub(_sub, _read_template(template))


def esc(value) -> str:
    return html.escape(str(value))


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def initials(name: str) -> str:
    parts = [p for p in re.split(r"\s+", name.strip()) if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def pct_text(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}%"


def level_of(value: float, vmin: float, vmax: float) -> int:
    """Lượng tử hóa value về 5 mức rời rạc 0..4 (không nội suy gradient)."""
    if vmax <= vmin:
        return 0
    ratio = (value - vmin) / (vmax - vmin)
    return max(0, min(4, int(ratio * 5)))


# ---------- khung ứng dụng ----------
def brand_html() -> str:
    return render("sidebar_brand", app_name=T.APP_NAME, tagline=T.APP_TAGLINE)


def sidebar_user_html(user) -> str:
    role = T.ROLE_ADMIN_VI if user.is_admin else T.ROLE_USER_VI
    return render("sidebar_user", initials=initials(user.name), name=user.name, role_label=role)


def topbar_html(crumbs: Sequence[str], user) -> str:
    parts = []
    for i, crumb in enumerate(crumbs):
        if i:
            parts.append('<span class="ev-icon ev-icon-sm ev-crumb-sep">chevron_right</span>')
        last = " ev-crumb-last" if i == len(crumbs) - 1 else ""
        parts.append(f'<span class="ev-crumb{last}">{esc(crumb)}</span>')
    return render(
        "topbar",
        breadcrumb_html="".join(parts),
        status_text=T.SYSTEM_READY,
        initials=initials(user.name),
        name=user.name,
    )


def page_header_html(eyebrow: str, title: str, subtitle: str, aside_html: str = "") -> str:
    return render("page_header", eyebrow=eyebrow, title=title, subtitle=subtitle, aside_html=aside_html)


def login_navbar_html() -> str:
    return render("login_navbar", app_name=T.APP_NAME, description=T.APP_DESCRIPTION, about=T.LOGIN_NAV_ABOUT, guide=T.LOGIN_NAV_GUIDE, login=T.TAB_LOGIN)


def login_hero_html() -> str:
    chips = []
    positions = [("happy", "tl"), ("angry", "tr"), ("sad", "bl"), ("surprised", "br")]
    for key, pos in positions:
        color = EMOTION_COLORS[key]
        chips.append(
            f'<div class="ev-login-chip ev-pos-{pos}" style="background:{hex_to_rgba(color, 0.2)};border-color:{hex_to_rgba(color, 0.4)};">'
            f'<span class="ev-dot" style="background:{color};"></span><span>{esc(T.EMOTION_VI[key])}</span></div>'
        )
    points = "".join(
        f'<li><span class="ev-check"><span class="ev-icon ev-icon-sm">check</span></span><span>{esc(p)}</span></li>' for p in T.LOGIN_HERO_POINTS
    )
    return render("login_hero", chips_html="".join(chips), title=T.LOGIN_HERO_TITLE, subtitle=T.LOGIN_HERO_SUB, points_html=points)


def auth_title_html(title: str, subtitle: str, error: str = "") -> str:
    err = f'<div class="ev-inline-error"><span class="ev-icon ev-icon-sm">error</span><span>{esc(error)}</span></div>' if error else ""
    return f'<div class="ev ev-auth-title"><h2 class="ev-h2">{esc(title)}</h2><p class="ev-sub">{esc(subtitle)}</p>{err}</div>'


def message_html(text: str, kind: str = "error") -> str:
    if not text:
        return ""
    icon = {"error": "error", "success": "check_circle", "info": "info"}.get(kind, "info")
    return f'<div class="ev ev-inline-msg ev-msg-{kind}"><span class="ev-icon ev-icon-sm">{icon}</span><span>{esc(text)}</span></div>'


# ---------- Phân tích mới ----------
def stepper_html(stage: str) -> str:
    active = {"input": 0, "processing": 1, "result": 3}[stage]
    done_until = {"input": 0, "processing": 1, "result": 3}[stage]
    subs = T.STEPPER_SUBS[stage]
    steps = []
    for i, title in enumerate(T.STEPPER_TITLES):
        state = "done" if i < done_until else ("active" if i == active else "todo")
        mark = '<span class="ev-icon ev-icon-sm">check</span>' if state == "done" else str(i + 1)
        steps.append(
            f'<div class="ev-step ev-step-{state}"><div class="ev-step-num">{mark}</div>'
            f'<div class="ev-step-text"><span class="ev-step-title">{esc(title)}</span><span class="ev-step-sub">{esc(subs[i])}</span></div></div>'
        )
        if i < len(T.STEPPER_TITLES) - 1:
            steps.append('<div class="ev-step-line"></div>')
    return render("stepper", eyebrow=T.STEPPER_EYEBROW, title=T.STEPPER_TITLE, steps_html="".join(steps))


def preprocess_chips_html() -> str:
    chips = "".join(f'<div class="ev-chip-sq"><span class="ev-dot ev-dot-teal ev-dot-sm"></span><span>{c}</span></div>' for c in T.PREPROC_CHIPS)
    return f'<div class="ev ev-preproc"><span class="ev-eyebrow">{esc(T.PREPROC_TITLE)}</span><div class="ev-chip-row">{chips}</div></div>'


def toast_html(kind: str, title: str, text: str, code: str = "") -> str:
    icon = {"error": "error", "warning": "mic_off", "info": "volume_off", "success": "check_circle"}.get(kind, "info")
    return render("toast", kind=kind, icon=icon, title=title, text=text, code=code)


def diagnostics_html(extra_toast: str = "") -> str:
    toasts = extra_toast or "".join(
        [
            toast_html("error", T.TOAST_FORMAT_TITLE, T.TOAST_FORMAT_TEXT, "UC02-E1"),
            toast_html("warning", T.TOAST_MIC_TITLE, T.TOAST_MIC_TEXT, "UC03-W1"),
            toast_html("info", T.TOAST_VAD_TITLE, T.TOAST_VAD_TEXT, "VAD-Null"),
        ]
    )
    head = f'<div class="ev-diag-head"><span class="ev-eyebrow">{esc(T.DIAG_TITLE)}</span><span class="ev-tag">{esc(T.DIAG_SAMPLE_TAG)}</span></div>'
    return f'<div class="ev ev-diag">{head}{toasts}</div>'


def params_card_html(snr: str, f0: str, zcr: str) -> str:
    return (
        f'<div class="ev ev-card ev-params"><span class="ev-eyebrow">{esc(T.PARAMS_TITLE)}</span>'
        f'<div class="ev-params-grid"><div class="ev-param"><span class="ev-meta">{esc(T.PARAM_SNR)}</span><span class="ev-param-val">{esc(snr)}</span></div>'
        f'<div class="ev-param"><span class="ev-meta">{esc(T.PARAM_F0)}</span><span class="ev-param-val">{esc(f0)}</span></div></div>'
        f'<div class="ev-param ev-param-wide"><span class="ev-meta">{esc(T.PARAM_ZCR)}</span><span class="ev-param-val-sm">{esc(zcr)}</span></div></div>'
    )


def processing_html(done: int) -> str:
    items = []
    for i, label in enumerate(T.PROCESSING_STEPS):
        state = "done" if i < done else ("active" if i == done else "todo")
        icon = "check_circle" if state == "done" else ("progress_activity" if state == "active" else "radio_button_unchecked")
        items.append(f'<li class="ev-check-{state}"><span class="ev-icon ev-icon-sm">{icon}</span><span>{esc(label)}</span></li>')
    return render("processing_checklist", title=T.PROCESSING_TITLE, items_html="".join(items))


# ---------- Kết quả + XAI ----------
def emotion_bars_html(probs: Sequence[float]) -> str:
    order = sorted(range(len(EMOTION_NAMES)), key=lambda i: probs[i], reverse=True)
    rows = []
    for rank, idx in enumerate(order):
        key = EMOTION_NAMES[idx]
        width = max(probs[idx] * 100.0, 0.5)
        strong = " ev-strong" if rank == 0 else ""
        rows.append(
            f'<div class="ev-bar-row"><span class="ev-bar-label{strong}">{esc(T.EMOTION_VI[key])}</span>'
            f'<div class="ev-track"><div class="ev-fill" style="width:{width:.1f}%;background:{EMOTION_COLORS[key]};"></div></div>'
            f'<span class="ev-bar-pct ev-tnum{strong}">{probs[idx] * 100:.0f}%</span></div>'
        )
    return render(
        "emotion_bars",
        title=T.BARS_TITLE,
        subtitle=T.BARS_SUB,
        sum_text=f"∑ p = {sum(probs):.2f}",
        rows_html="".join(rows),
        footer="",
    )


def emotion_hero_html(probs: Sequence[float], peak_range: Sequence[float], real_duration: float, threshold: float) -> str:
    top = max(range(len(probs)), key=lambda i: probs[i])
    key = EMOTION_NAMES[top]
    color = EMOTION_COLORS[key]
    conf = probs[top] * 100
    return render(
        "emotion_hero",
        eyebrow=T.HERO_EYEBROW,
        eyebrow_sub=T.HERO_EYEBROW_SUB,
        badge=T.AROUSAL_VI[key],
        tint=hex_to_rgba(color, 0.15),
        color=color,
        chip_text=T.HERO_LABEL_CHIP,
        label_vi=T.EMOTION_VI[key],
        label_en=key.capitalize(),
        icon=EMOTION_ICONS[key],
        confidence_label=T.CONFIDENCE,
        confidence_text=f"{conf:.1f}%",
        confidence_width=f"{conf:.1f}",
        tooltip=T.CONFIDENCE_TOOLTIP,
        threshold_text=T.CONFIDENCE_THRESHOLD.format(pct=int(threshold * 100)),
        description=T.HERO_DESC.format(label=T.EMOTION_VI[key], conf=f"{conf:.1f}%", t0=f"{peak_range[0]:.1f}", t1=f"{peak_range[1]:.1f}"),
        foot_left=T.HERO_FOOT_LEFT,
        foot_right=T.HERO_FOOT_RIGHT.format(sec=f"{real_duration:.1f}"),
    )


def demo_waveform(n: int = 60, voiced_ratio: float = 0.8) -> List[float]:
    """Biên độ giả lập xác định (không ngẫu nhiên) cho khung tĩnh; thay bằng waveform thật ở UC04."""
    out = []
    for i in range(n):
        if i / n > voiced_ratio:
            out.append(0.05 + 0.03 * abs(math.sin(i)))
        else:
            out.append(0.2 + 0.8 * abs(math.sin(i * 0.9) * math.cos(i * 0.31)))
    return out


def heatmap_html(levels: Sequence[int], amplitudes: Sequence[float], real_duration: float, total: float = 3.0) -> str:
    n_cells = len(levels)
    cell_sec = total / n_cells
    cells = "".join(
        f'<div class="ev-heat-cell" style="background:{HEAT_LEVELS[lv]};" title="{i * cell_sec:.1f}s–{(i + 1) * cell_sec:.1f}s: {esc(T.XAI_LEVELS[lv])}"></div>'
        for i, lv in enumerate(levels)
    )
    wave = []
    n_bars = len(amplitudes)
    for i, amp in enumerate(amplitudes):
        t = (i + 0.5) / n_bars * total
        lv = levels[min(int(t / cell_sec), n_cells - 1)]
        color = "#4361D8" if lv >= 3 else "#C5D1F7"
        wave.append(f'<span class="ev-wave-bar" style="height:{max(amp, 0.04) * 100:.0f}%;background:{color};"></span>')
    legend = "".join(f'<span class="ev-legend-cell" style="background:{c};" title="{esc(T.XAI_LEVELS[i])}"></span>' for i, c in enumerate(HEAT_LEVELS))
    marks = [0.0, 0.5, 1.0, 1.5, 2.0, real_duration, total]
    axis = "".join(
        f'<span class="{"ev-axis-real" if abs(m - real_duration) < 1e-9 else ""}">{m:.1f}s</span>'
        for m in sorted(set(round(m, 2) for m in marks))
    )
    left = real_duration / total * 100
    marker = (
        f'<div class="ev-real-end" style="left:{left:.1f}%;"><span class="ev-real-end-label">{esc(T.XAI_REAL_END.format(sec=f"{real_duration:.1f}"))}</span></div>'
    )
    return render(
        "heatmap_strip",
        title=T.XAI_TITLE,
        subtitle=T.XAI_SUB,
        legend_label=T.XAI_LEGEND,
        legend_cells_html=legend,
        legend_range=T.XAI_LEGEND_RANGE,
        marker_html=marker,
        wave_html="".join(wave),
        cells_html=cells,
        axis_html=axis,
        note_html=T.XAI_NOTE,
    )


def banner_html(kind: str, title: str, text: str) -> str:
    icon = {"warning": "warning", "info": "info", "success": "check_circle"}.get(kind, "info")
    return render("banner", kind=kind, icon=icon, title=title, text=text)


# ---------- bảng / chip dùng trong Dataframe (datatype html) ----------
def emotion_chip_html(key: str) -> str:
    color = EMOTION_COLORS[key]
    return (
        f'<span class="ev-chip" style="background:{hex_to_rgba(color, 0.15)};"><span class="ev-dot" style="background:{color};"></span>'
        f"{esc(T.EMOTION_VI[key])}</span>"
    )


def confidence_cell_html(pct: float) -> str:
    return f'<div class="ev-conf-cell"><span class="ev-tnum">{pct:.1f}%</span><div class="ev-track ev-track-sm"><div class="ev-fill ev-fill-primary" style="width:{pct:.1f}%;"></div></div></div>'


def audio_file_cell_html(name: str, duration: str) -> str:
    return (
        f'<div class="ev-file-cell"><span class="ev-file-icon"><span class="ev-icon ev-icon-sm">audio_file</span></span>'
        f'<div><div class="ev-file-name">{esc(name)}</div><div class="ev-meta">{esc(duration)}</div></div></div>'
    )


def level_chip_html(level: str) -> str:
    tone = {"INFO": "info", "WARNING": "warning", "ERROR": "error"}.get(level, "info")
    return f'<span class="ev-level ev-level-{tone}">{esc(level)}</span>'


def role_chip_html(role: str) -> str:
    label = T.ROLE_ADMIN_VI if role == "Admin" else T.ROLE_USER_VI
    cls = "ev-role-admin" if role == "Admin" else "ev-role-user"
    return f'<span class="ev-role-pill {cls}">{esc(label)}</span>'


def state_chip_html(active: bool) -> str:
    label = T.STATE_ACTIVE if active else T.STATE_LOCKED
    cls = "ev-state-on" if active else "ev-state-off"
    return f'<span class="ev-state-pill {cls}"><span class="ev-dot ev-dot-sm"></span>{esc(label)}</span>'


# ---------- KPI / trạng thái / rỗng ----------
def kpi_card_html(label: str, icon: str, value_html: str, sub_html: str = "") -> str:
    return render("kpi_card", label=label, icon=icon, value_html=value_html, sub_html=sub_html)


def status_row_html(name: str, description: str, tone: str, status_text: str, metric: str, icon: str = "check_circle") -> str:
    return render("status_row", name=name, description=description, tone=tone, status_text=status_text, metric=metric, icon=icon)


def empty_state_html(icon: str, title: str, text: str) -> str:
    return render("empty_state", icon=icon, title=title, text=text)


def tag_html(text: str) -> str:
    return f'<span class="ev-tag">{esc(text)}</span>'


# ---------- Mô hình & hiệu năng (đọc từ assets/metrics) ----------
def _fmt(value: Optional[float], unit: str = "", digits: int = 2) -> str:
    return T.CHART_NOT_MEASURED if value is None else f"{value:.{digits}f}{unit}"


def model_hero_html(model: Dict[str, object], dataset: str) -> str:
    acc, f1 = model.get("accuracy"), model.get("macro_f1")
    ratio, size, lat = model.get("trainable_ratio_pct"), model.get("size_mib"), model.get("latency_ms")
    pt, ptot = model.get("params_trainable"), model.get("params_total")

    def card(label: str, icon: str, value: str, bar: Optional[float], note: str) -> str:
        bar_html = f'<div class="ev-track ev-track-sm"><div class="ev-fill ev-fill-primary" style="width:{bar:.2f}%;"></div></div>' if bar is not None else ""
        return (
            f'<div class="ev-metric"><div class="ev-metric-top"><span class="ev-meta-strong">{esc(label)}</span><span class="ev-icon ev-icon-sm ev-icon-primary">{icon}</span></div>'
            f'<div class="ev-metric-val">{value}</div>{bar_html}<span class="ev-meta">{esc(note)}</span></div>'
        )

    cards = "".join(
        [
            card(T.METRIC_ACCURACY, "verified", f"{_fmt(acc, '', 2)}<small>%</small>" if acc is not None else esc(T.CHART_NOT_MEASURED), acc, dataset),
            card(T.METRIC_F1, "tune", f"{_fmt(f1, '', 2)}<small>%</small>" if f1 is not None else esc(T.CHART_NOT_MEASURED), f1, f"{model.get('model_type', '')}"),
            card(
                T.METRIC_TRAINABLE,
                "memory",
                f"{_fmt(ratio, '', 2)}<small>%</small>" if ratio is not None else esc(T.CHART_NOT_MEASURED),
                ratio,
                f"{pt:,} / {ptot:,}".replace(",", ".") if pt and ptot else "—",
            ),
            card(
                T.METRIC_SIZE_LATENCY,
                "speed",
                f"{_fmt(size, '', 1)}<small> MiB</small> <span class='ev-sep'>|</span> {_fmt(lat, '', 2)}<small> ms</small>",
                None,
                str(model.get("latency_note", "")),
            ),
        ]
    )
    return (
        f'<div class="ev ev-card ev-model-hero"><div class="ev-model-hero-top"><div class="ev-model-hero-icon"><span class="ev-icon ev-icon-xl">electric_bolt</span></div>'
        f'<div><div class="ev-model-hero-title"><h2 class="ev-h2">{esc(model["name"])}</h2><span class="ev-pill ev-pill-teal">{esc(T.MODELS_ACTIVE_TAG)}</span></div>'
        f'<p class="ev-sub">{esc(T.MODELS_HERO_DESC)}</p></div></div><div class="ev-metric-grid">{cards}</div></div>'
    )


def comparison_bars_html(title: str, unit: str, rows: Sequence[Dict[str, object]], key: str, active_key: str, digits: int, footer: str) -> str:
    present = [r[key] for r in rows if r.get(key) is not None]
    vmax = max(present) if present else 1.0
    items = []
    for r in rows:
        value = r.get(key)
        is_active = r["key"] == active_key
        cls = " ev-bar-active" if is_active else ""
        if value is None:
            items.append(
                f'<div class="ev-cmp-row"><div class="ev-cmp-top"><span class="ev-cmp-name">{esc(r["name"])}</span><span class="ev-meta">{esc(T.CHART_NOT_MEASURED)}</span></div>'
                f'<div class="ev-track ev-track-lg ev-track-empty"></div></div>'
            )
        else:
            width = max(value / vmax * 100.0, 1.0)
            items.append(
                f'<div class="ev-cmp-row{cls}"><div class="ev-cmp-top"><span class="ev-cmp-name">{esc(r["name"])}</span><span class="ev-cmp-val ev-tnum">{value:.{digits}f}</span></div>'
                f'<div class="ev-track ev-track-lg"><div class="ev-fill {"ev-fill-primary" if is_active else "ev-fill-tint"}" style="width:{width:.1f}%;"></div></div></div>'
            )
    return (
        f'<div class="ev ev-card ev-cmp"><div class="ev-card-head"><h3 class="ev-h3">{esc(title)}</h3><span class="ev-tag">{esc(unit)}</span></div>'
        f'<div class="ev-cmp-list">{"".join(items)}</div><div class="ev-cmp-foot ev-meta">{esc(footer)}</div></div>'
    )


def models_table_html(rows: Sequence[Dict[str, object]], active_key: str) -> str:
    head = "".join(
        f"<th>{esc(h)}</th>"
        for h in (T.COL_MODEL_NAME, T.COL_ARCH, "Accuracy", "Macro F1", "Dung lượng", "Độ trễ", T.COL_STATUS)
    )
    body = []
    for r in rows:
        active = r["key"] == active_key
        status = T.STATUS_LABELS.get(str(r.get("status")), "")
        body.append(
            f'<tr class="{"ev-row-active" if active else ""}"><td class="ev-td-name">{esc(r["name"])}</td><td><span class="ev-tag">{esc(r["model_type"])}</span></td>'
            f'<td class="ev-tnum">{_fmt(r.get("accuracy"), "%")}</td><td class="ev-tnum">{_fmt(r.get("macro_f1"), "%")}</td>'
            f'<td class="ev-tnum">{_fmt(r.get("size_mib"), " MiB", 1)}</td><td class="ev-tnum">{_fmt(r.get("latency_ms"), " ms")}</td>'
            f'<td><span class="ev-status-chip ev-status-{esc(r.get("status"))}">{esc(status)}</span></td></tr>'
        )
    return f'<div class="ev ev-table-wrap"><table class="ev-table"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def confusion_matrix_html(cm: Optional[Dict[str, object]]) -> str:
    if not cm or not cm.get("matrix_normalized"):
        return empty_state_html("grid_on", T.CM_TITLE, T.CM_NO_DATA)
    labels_vi: List[str] = cm["labels_vi"]  # type: ignore[assignment]
    matrix: List[List[float]] = cm["matrix_normalized"]  # type: ignore[assignment]
    head = '<div class="ev-cm-row"><div></div>' + "".join(f'<div class="ev-cm-col">{esc(l)}</div>' for l in labels_vi) + "</div>"
    rows = []
    for i, row in enumerate(matrix):
        cells = []
        for j, v in enumerate(row):
            lv = level_of(v, 0.0, 1.0001)
            diag = " ev-cm-diag" if i == j else ""
            cells.append(f'<div class="ev-cm-cell ev-heat-{lv}{diag}">{round(v * 100):d}%</div>')
        rows.append(f'<div class="ev-cm-row"><div class="ev-cm-rowlabel">{esc(labels_vi[i])}</div>{"".join(cells)}</div>')
    scale_labels = ["0–20%", "21–40%", "41–60%", "61–80%", "81–100%"]
    scale = "".join(f'<span class="ev-legend-cell ev-heat-{i}"></span><span class="ev-meta">{s}</span>' for i, s in enumerate(scale_labels))
    return (
        f'<div class="ev ev-cm"><div class="ev-cm-legend"><span class="ev-meta-strong">{esc(T.CM_SCALE)}</span>{scale}</div>'
        f'<div class="ev-cm-axis-x">{esc(T.CM_X_AXIS)}</div><div class="ev-cm-body"><div class="ev-cm-axis-y">{esc(T.CM_Y_AXIS)}</div>'
        f'<div class="ev-cm-grid">{head}{"".join(rows)}</div></div></div>'
    )


# ---------- drawer lịch sử + insight ----------
def mini_heatmap_html(levels: Sequence[int]) -> str:
    cells = "".join(f'<div class="ev-mini-cell" style="background:{HEAT_LEVELS[lv]};" title="{esc(T.XAI_LEVELS[lv])}"></div>' for lv in levels)
    legend = "".join(f'<span class="ev-legend-cell ev-legend-sm" style="background:{c};"></span>' for c in HEAT_LEVELS)
    return (
        f'<div class="ev ev-mini-heat"><div class="ev-mini-head"><span class="ev-meta-strong">{esc(T.DRAWER_HEATMAP)}</span><span class="ev-meta">{esc(T.DRAWER_HEATMAP_TAG)}</span></div>'
        f'<div class="ev-mini-grid">{cells}</div><div class="ev-mini-legend">{legend}</div></div>'
    )


def prob_bars_compact_html(probs: Sequence[float], top: int = 4) -> str:
    order = sorted(range(len(EMOTION_NAMES)), key=lambda i: probs[i], reverse=True)[:top]
    rows = []
    for rank, idx in enumerate(order):
        key = EMOTION_NAMES[idx]
        strong = " ev-strong" if rank == 0 else ""
        rows.append(
            f'<div class="ev-pc-row"><div class="ev-pc-top"><span class="{strong.strip()}">{esc(T.EMOTION_VI[key])}</span><span class="ev-tnum{strong}">{probs[idx] * 100:.1f}%</span></div>'
            f'<div class="ev-track ev-track-md"><div class="ev-fill" style="width:{max(probs[idx] * 100, 0.5):.1f}%;background:{EMOTION_COLORS[key]};"></div></div></div>'
        )
    return f'<div class="ev ev-pc"><span class="ev-meta-strong">{esc(T.DRAWER_PROBS)}</span>{"".join(rows)}</div>'


def drawer_head_html(filename: str, meta: str, emotion_key: str, confidence_pct: float) -> str:
    color = EMOTION_COLORS[emotion_key]
    return (
        f'<div class="ev ev-drawer-head"><div><div class="ev-eyebrow ev-eyebrow-primary"><span class="ev-icon ev-icon-sm">psychology</span> {esc(T.DRAWER_TITLE)}</div>'
        f'<div class="ev-drawer-title">{esc(filename)}</div><div class="ev-meta">{esc(meta)}</div></div>'
        f'<span class="ev-chip" style="background:{hex_to_rgba(color, 0.15)};">{esc(T.EMOTION_VI[emotion_key])} ({confidence_pct:.1f}%)</span></div>'
    )


def insight_html(icon: str, title: str, text: str) -> str:
    return (
        f'<div class="ev ev-insight"><span class="ev-icon ev-icon-primary ev-icon-lg">{icon}</span>'
        f'<div><div class="ev-meta-strong">{esc(title)}</div><p class="ev-sub">{esc(text)}</p></div></div>'
    )


def summary_badges_html(items: Sequence[Sequence[str]]) -> str:
    """items = [(nhãn, giá trị, màu chấm hex)]"""
    cells = "".join(
        f'<div class="ev-summary-item"><span class="ev-dot" style="background:{c};"></span><div class="ev-summary-text"><span class="ev-meta">{esc(label)}</span><span class="ev-summary-val">{esc(value)}</span></div></div>'
        for label, value, c in items
    )
    return f'<div class="ev ev-summary">{cells}</div>'
