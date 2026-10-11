# Topbar 64px theo Stitch: breadcrumb + chip "Hệ thống sẵn sàng" + chuông + avatar. Một gr.HTML, nội dung dựng lại mỗi lần đổi trang.
from typing import List

import gradio as gr

from core.session import SessionUser
from ui import i18n_vi as T
from ui import render


def build() -> "gr.HTML":
    return gr.HTML("", elem_id="ev-topbar", elem_classes=["ev-plain"])


def crumbs_for(page_label: str, admin_only: bool, extra: str = "") -> List[str]:
    crumbs = [T.BREADCRUMB_ADMIN if admin_only else T.BREADCRUMB_HOME, page_label]
    if extra:
        crumbs.append(extra)
    return crumbs


def render_topbar(page_label: str, admin_only: bool, user: SessionUser, extra: str = "") -> str:
    return render.topbar_html(crumbs_for(page_label, admin_only, extra), user)
