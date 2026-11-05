# Ô chọn khoảng ngày: MỘT ô chữ chỉ đọc + MỘT lịch (script trong ui/theme.py). Bấm ngày bắt đầu rồi ngày kết thúc để chọn khoảng; nháy đúp
# (hoặc bấm hai lần cùng một ngày) để chọn đúng một ngày. Lịch ghi kết quả vào ô dưới dạng "dd/mm/yyyy" hoặc "dd/mm/yyyy – dd/mm/yyyy".
# parse() đổi chuỗi đó thành (từ ngày, đến ngày) dạng 'YYYY-MM-DD' cho tầng dịch vụ; ô trống = không lọc theo ngày.
import re
from typing import Optional, Tuple

import gradio as gr

from ui import i18n_vi as T

SEP = " – "
_SPLIT = re.compile(r"\s+(?:–|-|~|→|đến)\s+")  # dấu phân cách có khoảng trắng hai bên; ngày ISO (2026-10-16) không bị tách vì dấu '-' dính liền số
_DMY = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")
_ISO = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")


def build(elem_id: str, **kwargs) -> gr.Textbox:
    """Ô hiển thị khoảng ngày đã chọn; script gắn nút lịch và khóa gõ tay. elem_id trùng data-for của dòng chú thích (render.date_hint_html)."""
    return gr.Textbox(placeholder=T.DATE_RANGE_PH, show_label=False, container=False, max_lines=1, elem_id=elem_id, elem_classes=["ev-field", "ev-range"], **kwargs)


def _to_iso(text: str) -> str:
    text = text.strip()
    match = _DMY.match(text)
    if match:
        day, month, year = (int(g) for g in match.groups())
    else:
        match = _ISO.match(text)
        if not match:
            raise ValueError(T.MSG_BAD_DATE_RANGE)
        year, month, day = (int(g) for g in match.groups())
    return f"{year:04d}-{month:02d}-{day:02d}"


def parse(text: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """'16/10/2026' -> ('2026-10-16', '2026-10-16'); '16/10/2026 – 20/10/2026' -> hai đầu; trống -> (None, None). Sai định dạng thì ném ValueError."""
    text = (text or "").strip()
    if not text:
        return None, None
    parts = _SPLIT.split(text)
    if len(parts) > 2:
        raise ValueError(T.MSG_BAD_DATE_RANGE)
    first = _to_iso(parts[0])
    return first, _to_iso(parts[1]) if len(parts) == 2 else first
