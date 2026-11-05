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
<script>
/* Lịch chọn khoảng ngày cho ô .ev-range (ui/components/daterange.py): bấm ngày bắt đầu rồi ngày kết thúc; nháy đúp (hoặc bấm hai lần cùng một ngày) chọn một ngày.
   Khóa ngày chưa tới và ngày trước ngày có dữ liệu đầu tiên (data-min của .ev-date-hint có data-for chứa id của ô). Kết quả ghi vào ô: dd/mm/yyyy hoặc dd/mm/yyyy – dd/mm/yyyy. */
(function () {
  var WEEK = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'], SEP = ' – ';
  var ICON = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="18"></rect><line x1="2" y1="9" x2="22" y2="9"></line><line x1="7" y1="2" x2="7" y2="6"></line><line x1="17" y1="2" x2="17" y2="6"></line></svg>';
  var pop = null, cur = null;
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function key(d) { return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }
  function fmt(d) { return pad(d.getDate()) + '/' + pad(d.getMonth() + 1) + '/' + d.getFullYear(); }
  function fromKey(s) { var p = s.split('-'); return new Date(+p[0], +p[1] - 1, +p[2]); }
  function today() { var n = new Date(); return new Date(n.getFullYear(), n.getMonth(), n.getDate()); }
  function parseOne(t) {
    var p = t.trim().split('/'), d;
    if (p.length !== 3) return null;
    d = new Date(+p[2], +p[1] - 1, +p[0]);
    return isNaN(d.getTime()) ? null : d;
  }
  function parseValue(v) {
    var parts = (v || '').split(SEP), a = parseOne(parts[0] || ''), b = parts.length > 1 ? parseOne(parts[1]) : a;
    return a ? { start: a, end: b || a } : null;
  }
  function minOf(block) {
    var hints = document.querySelectorAll('.ev-date-hint'), i, m;
    for (i = 0; i < hints.length; i++) {
      if ((hints[i].getAttribute('data-for') || '').split(' ').indexOf(block.id) >= 0) {
        m = hints[i].getAttribute('data-min');
        return m ? fromKey(m) : null;
      }
    }
    return null;
  }
  function close() { if (pop) { pop.remove(); pop = null; } cur = null; }
  function commit(a, b) {
    var input = cur.input, lo = a <= b ? a : b, hi = a <= b ? b : a;
    input.value = key(lo) === key(hi) ? fmt(lo) : fmt(lo) + SEP + fmt(hi);
    input.dispatchEvent(new Event('input', { bubbles: true }));
    close();
  }
  function paint() {
    if (!pop) return;
    var days = pop.querySelectorAll('button.ev-rp-day'), end = cur.end || cur.hover, i, k, lo, hi, cls;
    lo = cur.start && end ? (cur.start <= end ? cur.start : end) : cur.start;
    hi = cur.start && end ? (cur.start <= end ? end : cur.start) : cur.start;
    for (i = 0; i < days.length; i++) {
      k = fromKey(days[i].getAttribute('data-d'));
      days[i].classList.toggle('is-edge', !!lo && (k.getTime() === lo.getTime() || k.getTime() === hi.getTime()));
      days[i].classList.toggle('in-range', !!lo && k > lo && k < hi);
    }
    pop.querySelector('.ev-rp-help').textContent = !cur.start || cur.end ? 'Bấm ngày bắt đầu (nháy đúp để chọn một ngày)' : 'Bấm ngày kết thúc (bấm lại cùng ngày để chọn một ngày)';
  }
  function render() {
    var c = cur, t = today(), min = minOf(c.block), first = new Date(c.y, c.m, 1), html = '', i, d, off, other, prevOff, nextOff;
    prevOff = !!min && (c.y * 12 + c.m <= min.getFullYear() * 12 + min.getMonth());
    nextOff = c.y * 12 + c.m >= t.getFullYear() * 12 + t.getMonth();
    html += '<div class="ev-rp-head"><button type="button" class="ev-rp-nav" data-nav="-1"' + (prevOff ? ' disabled' : '') + '>‹</button><span>Tháng ' + (c.m + 1) + ' / ' + c.y + '</span><button type="button" class="ev-rp-nav" data-nav="1"' + (nextOff ? ' disabled' : '') + '>›</button></div>';
    html += '<div class="ev-rp-week">';
    for (i = 0; i < 7; i++) html += '<span>' + WEEK[i] + '</span>';
    html += '</div><div class="ev-rp-days">';
    for (i = 0; i < 42; i++) {
      d = new Date(c.y, c.m, 1 - first.getDay() + i);
      other = d.getMonth() !== c.m;
      off = d > t || (!!min && d < min);
      html += '<button type="button" class="ev-rp-day' + (other ? ' other' : '') + (off ? ' off' : '') + '" data-d="' + key(d) + '"' + (off ? ' disabled' : '') + '>' + d.getDate() + '</button>';
    }
    html += '</div><div class="ev-rp-help"></div><div class="ev-rp-foot"><button type="button" data-act="clear">Xóa lọc ngày</button><button type="button" data-act="today">Hôm nay</button></div>';
    pop.innerHTML = html;
    paint();
  }
  function open(block) {
    var input = block.querySelector('input, textarea'), v = parseValue(input.value), t = today(), r = input.getBoundingClientRect(), base = v ? v.start : t;
    close();
    cur = { block: block, input: input, start: v ? v.start : null, end: v ? v.end : null, hover: null, y: base.getFullYear(), m: base.getMonth() };
    pop = document.createElement('div');
    pop.className = 'ev-rangepop';
    pop.style.top = (r.bottom + 6) + 'px';
    pop.style.left = Math.max(8, Math.min(r.left, window.innerWidth - 308)) + 'px';
    (block.closest('#view-app') || document.body).appendChild(pop);  /* đặt trong #view-app để dùng bộ biến màu --ev-* của giao diện */
    render();
  }
  function pick(d) {
    if (!cur.start || cur.end) { cur.start = d; cur.end = null; cur.hover = null; paint(); return; }
    commit(cur.start, d);
  }
  document.addEventListener('click', function (e) {
    var t = e.target, b = t.closest && t.closest('.ev-range'), btn, nav, act;
    if (pop && pop.contains(t)) {
      btn = t.closest('button');
      if (!btn || btn.disabled) return;
      if (btn.hasAttribute('data-d')) { pick(fromKey(btn.getAttribute('data-d'))); return; }
      nav = btn.getAttribute('data-nav');
      if (nav) { cur.m += parseInt(nav, 10); if (cur.m < 0) { cur.m = 11; cur.y -= 1; } else if (cur.m > 11) { cur.m = 0; cur.y += 1; } render(); return; }
      act = btn.getAttribute('data-act');
      if (act === 'today') commit(today(), today());
      else if (act === 'clear') { cur.input.value = ''; cur.input.dispatchEvent(new Event('input', { bubbles: true })); close(); }
      return;
    }
    if (b) { if (pop && cur && cur.block === b) close(); else open(b); return; }
    close();
  });
  document.addEventListener('dblclick', function (e) {
    var btn = pop && e.target.closest ? e.target.closest('button.ev-rp-day') : null;
    if (btn && !btn.disabled) { var d = fromKey(btn.getAttribute('data-d')); commit(d, d); }
  });
  document.addEventListener('mouseover', function (e) {
    var btn = pop && cur && cur.start && !cur.end && e.target.closest ? e.target.closest('button.ev-rp-day') : null;
    if (btn && !btn.disabled) { cur.hover = fromKey(btn.getAttribute('data-d')); paint(); }
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
  window.addEventListener('resize', close);
  window.addEventListener('scroll', function (e) { if (pop && !pop.contains(e.target)) close(); }, true);
  /* gắn biểu tượng lịch và khóa gõ tay cho các ô .ev-range mới xuất hiện */
  var queued = false;
  function scan() {
    queued = false;
    var blocks = document.querySelectorAll('.ev-range'), i, input, ico;
    for (i = 0; i < blocks.length; i++) {
      input = blocks[i].querySelector('input, textarea');
      if (input && !input.readOnly) input.readOnly = true;
      if (!blocks[i].querySelector('.ev-range-ico')) {
        ico = document.createElement('span');
        ico.className = 'ev-range-ico';
        ico.innerHTML = ICON;
        blocks[i].appendChild(ico);
      }
    }
  }
  function start() {
    new MutationObserver(function () { if (!queued) { queued = true; requestAnimationFrame(scan); } }).observe(document.body, { childList: true, subtree: true });
    scan();
  }
  if (document.body) start(); else document.addEventListener('DOMContentLoaded', start);
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
