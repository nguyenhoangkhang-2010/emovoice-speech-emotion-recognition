# Theme Gradio + CSS + head. Ép chế độ sáng (không dark mode), không gradient.
# Gradio 6 chuyển theme/css/head từ gr.Blocks() sang launch(): app_kwargs() tự phát hiện bằng inspect nên chạy được cả gradio 5 lẫn 6.
import inspect
from pathlib import Path
from typing import Dict, Tuple

CSS_DIR = Path(__file__).resolve().parent / "css"
CSS_FILES = ("tokens.css", "stitch.css", "shell.css", "components.css", "pages.css", "auth.css")

BG, CARD, ALT, BORDER = "#F4F6FB", "#FFFFFF", "#EEF1F8", "#DCE2F0"
PRIMARY, HOVER, TINT, TINT2 = "#4361D8", "#3047B0", "#E8EDFC", "#C5D1F7"
TEXT, BODY, MUTED = "#2F3E63", "#4A5878", "#7A88A6"
SHADOW_1 = "0 2px 8px rgba(67, 97, 216, 0.04)"
SHADOW_2 = "0 8px 24px rgba(67, 97, 216, 0.08)"

HEAD_HTML = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300;0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">
<script>
(function () {
  try {
    var u = new URL(window.location.href);
    if (u.searchParams.get('__theme') !== 'light') { u.searchParams.set('__theme', 'light'); window.location.replace(u.toString()); }
  } catch (e) {}
})();
</script>
<script>
/* Popup (.ev-modal): Esc hoặc bấm vào nền mờ thì bấm nút .ev-modal-close của popup đang mở */
(function () {
  function openModal() {
    var all = document.querySelectorAll('.ev-modal');
    for (var i = 0; i < all.length; i++) { if (getComputedStyle(all[i]).display !== 'none') return all[i]; }
    return null;
  }
  function close(modal) { var b = modal && modal.querySelector('.ev-modal-close'); if (b) b.click(); }
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(openModal()); });
  document.addEventListener('click', function (e) {
    var t = e.target;
    if (t && t.classList && t.classList.contains('ev-modal')) close(t);
  });
})();
</script>
"""

THEME_TOKENS: Dict[str, str] = {
    "body_background_fill": BG,
    "body_text_color": BODY,
    "body_text_color_subdued": MUTED,
    "background_fill_primary": CARD,
    "background_fill_secondary": ALT,
    "border_color_primary": BORDER,
    "border_color_accent": TINT2,
    "color_accent_soft": TINT,
    "block_background_fill": CARD,
    "block_border_color": BORDER,
    "block_border_width": "1px",
    "block_radius": "16px",
    "block_shadow": SHADOW_1,
    "block_label_background_fill": ALT,
    "block_label_text_color": BODY,
    "block_title_text_color": TEXT,
    "block_info_text_color": MUTED,
    "panel_background_fill": ALT,
    "panel_border_color": BORDER,
    "input_background_fill": CARD,
    "input_border_color": BORDER,
    "input_border_color_focus": PRIMARY,
    "input_radius": "12px",
    "input_shadow": "none",
    "input_shadow_focus": f"0 0 0 3px {TINT}",
    "input_placeholder_color": MUTED,
    "button_primary_background_fill": PRIMARY,
    "button_primary_background_fill_hover": HOVER,
    "button_primary_text_color": "#FFFFFF",
    "button_primary_border_color": PRIMARY,
    "button_primary_shadow": "none",
    "button_secondary_background_fill": CARD,
    "button_secondary_background_fill_hover": ALT,
    "button_secondary_text_color": TEXT,
    "button_secondary_border_color": BORDER,
    "button_secondary_shadow": "none",
    "button_large_radius": "12px",
    "button_medium_radius": "12px",
    "button_small_radius": "8px",
    "shadow_drop": SHADOW_1,
    "shadow_drop_lg": SHADOW_2,
    "shadow_spread": "0px",
    "checkbox_background_color": CARD,
    "checkbox_background_color_selected": PRIMARY,
    "checkbox_border_color": BORDER,
    "checkbox_border_color_selected": PRIMARY,
    "checkbox_label_text_color": BODY,
    "link_text_color": PRIMARY,
    "link_text_color_hover": HOVER,
    "table_even_background_fill": CARD,
    "table_odd_background_fill": CARD,
    "table_border_color": BORDER,
    "loader_color": PRIMARY,
    "slider_color": PRIMARY,
}


def load_css() -> str:
    from core.config import settings

    css = "\n".join((CSS_DIR / name).read_text(encoding="utf-8") for name in CSS_FILES)
    hint = f"Thời lượng khuyến nghị 1 – 5 giây, dung lượng tối đa {settings.max_upload_mb} MB."  # chữ trong vùng kéo thả lấy từ cấu hình
    return css + f'\n.ev-audio-drop button.upload-container::after {{ content: "{hint}"; }}\n'


def build_theme():
    import gradio as gr

    primary = gr.themes.Color(
        name="ev_primary", c50=TINT, c100=TINT, c200=TINT2, c300="#9DB1F0", c400="#6F89E6", c500=PRIMARY,
        c600=PRIMARY, c700=HOVER, c800=HOVER, c900=TEXT, c950=TEXT,
    )
    neutral = gr.themes.Color(
        name="ev_navy", c50=BG, c100=ALT, c200=BORDER, c300="#C5CCE0", c400="#A3AFCB", c500=MUTED,
        c600="#6A7899", c700=BODY, c800="#3B4A6E", c900=TEXT, c950=TEXT,
    )
    theme = gr.themes.Base(primary_hue=primary, secondary_hue=primary, neutral_hue=neutral, font=("Inter", "Be Vietnam Pro", "sans-serif"))
    allowed = set(inspect.signature(theme.set).parameters)
    tokens: Dict[str, str] = {}
    for key, value in THEME_TOKENS.items():
        if key in allowed:
            tokens[key] = value
        if f"{key}_dark" in allowed:  # dark = light: không có chế độ tối
            tokens[f"{key}_dark"] = value
    return theme.set(**tokens)


def app_kwargs() -> Tuple[dict, dict]:
    """Trả (kwargs cho gr.Blocks, kwargs cho launch) tùy phiên bản gradio."""
    import gradio as gr

    shared = {"theme": build_theme(), "css": load_css(), "head": HEAD_HTML}
    launch_params = set(inspect.signature(gr.Blocks.launch).parameters)
    if {"theme", "css", "head"} <= launch_params:
        return {}, shared
    return shared, {}
