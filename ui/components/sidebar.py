# Sidebar 260px theo Stitch (brand, nhóm menu, thẻ người dùng, đăng xuất). Menu là gr.Button gán elem_classes; trạng thái active do ui/layout.show_page cập nhật.
# Nhóm "Quản trị hệ thống" nằm trong Column ẩn mặc định, chỉ bật cho Admin khi đăng nhập; handler admin vẫn tự gọi require_admin.
from typing import Dict, List, Sequence, Tuple

import gradio as gr

from ui import i18n_vi as T
from ui import render

NavGroup = Tuple[str, Sequence[Tuple[str, str]], bool]  # (nhãn nhóm, [(page, nhãn)], chỉ admin)


def _nav_button(page: str, label: str) -> "gr.Button":
    return gr.Button(label, elem_id=f"nav-{page}", elem_classes=["ev-nav-btn"], variant="secondary")


def build(groups: Sequence[NavGroup]) -> Dict[str, object]:
    buttons: Dict[str, "gr.Button"] = {}
    admin_group = None
    with gr.Column(elem_id="ev-sidebar") as column:
        with gr.Column(elem_classes=["ev-side-nav"]):
            gr.HTML(render.brand_html(), elem_classes=["ev-plain"])
            for label, items, admin_only in groups:
                if admin_only:
                    with gr.Column(visible=False, elem_id="ev-admin-group", elem_classes=["ev-side-nav"]) as admin_group:
                        gr.HTML(f'<div class="ev ev-nav-group">{render.esc(label)}</div>', elem_classes=["ev-plain"])
                        for page, text in items:
                            buttons[page] = _nav_button(page, text)
                else:
                    gr.HTML(f'<div class="ev ev-nav-group">{render.esc(label)}</div>', elem_classes=["ev-plain"])
                    for page, text in items:
                        buttons[page] = _nav_button(page, text)
        with gr.Column(elem_classes=["ev-side-footer"]):
            user_card = gr.HTML("", elem_classes=["ev-plain"])
            logout = gr.Button(T.LOGOUT, elem_id="ev-logout", elem_classes=["ev-logout-btn"], variant="secondary")
    return {"column": column, "buttons": buttons, "admin_group": admin_group, "user_card": user_card, "logout": logout}
