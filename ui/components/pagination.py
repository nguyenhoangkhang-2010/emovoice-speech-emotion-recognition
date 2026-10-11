# Phân trang mô phỏng bảng Stitch: State số trang + nút Trước / số trang / Sau + chọn số dòng mỗi trang.
# Gradio không có control phân trang sẵn nên dựng bằng gr.Button; xem docs/ui-pages.md mục "Chỗ Gradio không dựng y hệt Stitch".
import math
from typing import Callable, Dict, List, Sequence, Tuple

import gradio as gr

from ui import i18n_vi as T

WINDOW = 5
PAGE_SIZES = [10, 20, 50]


def build(default_size: int = 10) -> Dict[str, object]:
    state = gr.State(1)
    total = gr.State(0)
    with gr.Row(elem_classes=["ev-pagination"]):
        info = gr.HTML("", elem_classes=["ev-plain"])
        size = gr.Dropdown(PAGE_SIZES, value=default_size, label=T.PAGINATION_PAGE_SIZE, elem_classes=["ev-field", "ev-select"], scale=0, min_width=160)
        prev = gr.Button(f"‹ {T.PAGINATION_PREV}", elem_classes=["ev-page-btn", "ev-page-nav"], scale=0, min_width=70)
        nums = [gr.Button(str(i + 1), elem_classes=["ev-page-btn"], scale=0, min_width=32, visible=(i == 0)) for i in range(WINDOW)]
        nxt = gr.Button(f"{T.PAGINATION_NEXT} ›", elem_classes=["ev-page-btn", "ev-page-nav"], scale=0, min_width=70)
    return {"state": state, "total": total, "info": info, "size": size, "prev": prev, "nums": nums, "next": nxt}


def controls(pg: Dict[str, object]) -> List[object]:
    """Thứ tự component được cập nhật bởi view()."""
    return [pg["state"], pg["total"], pg["info"], pg["prev"], *pg["nums"], pg["next"]]


def last_page(total: int, size: int) -> int:
    return max(1, math.ceil(total / size)) if size else 1


def view(page: int, total: int, size: int) -> List[object]:
    last = last_page(total, size)
    page = max(1, min(page, last))
    start = max(1, min(page - WINDOW // 2, last - WINDOW + 1))
    shown = list(range(start, min(last, start + WINDOW - 1) + 1))
    first_row = (page - 1) * size + 1 if total else 0
    last_row = min(page * size, total)
    info_html = f'<div class="ev ev-page-info">{T.PAGINATION_INFO.format(start=first_row, end=last_row, total=total)}</div>'
    num_updates = []
    for i in range(WINDOW):
        if i < len(shown):
            n = shown[i]
            num_updates.append(gr.update(value=str(n), visible=True, variant="primary" if n == page else "secondary", elem_classes=["ev-page-btn", "active"] if n == page else ["ev-page-btn"]))
        else:
            num_updates.append(gr.update(visible=False))
    return [page, total, info_html, gr.update(interactive=page > 1), *num_updates, gr.update(interactive=page < last)]


def wire(
    pg: Dict[str, object],
    fetch: Callable[..., Tuple[int, Sequence[object]]],
    extra_inputs: Sequence[object] = (),
    extra_outputs: Sequence[object] = (),
) -> Callable[..., List[object]]:
    """fetch(page, size, *extra) -> (total, giá trị cho extra_outputs). Trả hàm khởi tạo để gọi lúc nạp trang."""
    outputs = controls(pg) + list(extra_outputs)
    base = [pg["state"], pg["total"], pg["size"]]

    def run(page: int, size: int, *extra) -> List[object]:
        total, values = fetch(page, size, *extra)
        return [*view(page, total, size), *values]

    pg["prev"].click(lambda p, t, s, *e: run(max(1, p - 1), s, *e), inputs=[*base, *extra_inputs], outputs=outputs)
    pg["next"].click(lambda p, t, s, *e: run(min(last_page(t, s), p + 1), s, *e), inputs=[*base, *extra_inputs], outputs=outputs)
    for btn in pg["nums"]:
        btn.click(lambda p, t, s, label, *e: run(int(label), s, *e), inputs=[*base, btn, *extra_inputs], outputs=outputs)
    pg["size"].change(lambda p, t, s, *e: run(1, s, *e), inputs=[*base, *extra_inputs], outputs=outputs)
    return run
