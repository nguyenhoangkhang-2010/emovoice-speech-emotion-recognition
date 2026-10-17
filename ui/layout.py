# Lắp ráp ứng dụng: view đăng nhập + view ứng dụng (sidebar, topbar, các Column trang). show_page() đổi trang và trạng thái active.
# Phân quyền: sidebar chỉ bật nhóm "Quản trị hệ thống" cho Admin; show_page chặn trang admin với người thường; mọi handler admin còn tự gọi guard_admin.
import logging

import gradio as gr

from core.session import PermissionDenied, require_admin, require_login
from services import auth_service
from ui import i18n_vi as T
from ui import render, theme
from ui.components import sidebar, topbar
from ui.pages import account, admin_audio, admin_logs, admin_models, admin_overview, admin_users, analyze, history, login, model_performance

PAGE_MODULES = [analyze, history, account, admin_overview, model_performance, admin_users, admin_logs, admin_models, admin_audio]
DEFAULT_PAGE = analyze.NAME
GROUP_LABELS = {"analysis": T.NAV_GROUP_ANALYSIS, "account": T.NAV_GROUP_ACCOUNT, "admin": T.NAV_GROUP_ADMIN}


def active_pages():
    from core.config import settings

    return [m for m in PAGE_MODULES if not m.EXTRA or settings.enable_admin_extra_pages]


def nav_groups(pages):
    groups = []
    for key in ("analysis", "account", "admin"):
        items = [(m.NAME, m.LABEL) for m in pages if m.GROUP == key]
        if items:
            groups.append((GROUP_LABELS[key], items, key == "admin"))
    return groups


def build_app() -> "gr.Blocks":
    pages = active_pages()
    by_name = {m.NAME: m for m in pages}
    blocks_kwargs, _ = theme.app_kwargs()

    with gr.Blocks(title=f"{T.APP_NAME} - {T.APP_DESCRIPTION}", **blocks_kwargs) as demo:
        session = gr.State(None)  # SessionUser sau đăng nhập; gr.State nằm phía server theo từng phiên trình duyệt

        auth = login.build(session)
        auth_view = auth["view"]

        with gr.Column(visible=False, elem_id="view-app") as app_view:
            with gr.Row(elem_id="ev-shell"):
                side = sidebar.build(nav_groups(pages))
                with gr.Column(elem_id="ev-main"):
                    top = topbar.build()
                    page_cols, page_parts = {}, {}
                    with gr.Column(elem_id="ev-content"):
                        for module in pages:
                            with gr.Column(visible=False, elem_id=f"page-{module.NAME}", elem_classes=["ev-page"]) as col:
                                page_parts[module.NAME] = module.build(session)
                            page_cols[module.NAME] = col
                    gr.HTML(render.app_footer_html(), elem_classes=["ev-plain"])

        nav_btns = side["buttons"]
        admin_group = side["admin_group"]
        user_card = side["user_card"]

        def page_updates(page_name, user):
            target = by_name.get(page_name) or by_name[DEFAULT_PAGE]
            try:
                require_admin(user) if target.ADMIN_ONLY else require_login(user)
            except PermissionDenied:
                target = by_name[DEFAULT_PAGE]  # người thường (hoặc chưa đăng nhập) không vào được trang admin
            updates = {page_cols[m.NAME]: gr.update(visible=m is target) for m in pages}
            for name, btn in nav_btns.items():
                on = name == target.NAME
                updates[btn] = gr.update(variant="primary" if on else "secondary", elem_classes=["ev-nav-btn", "active"] if on else ["ev-nav-btn"])
            if user is not None:
                updates[top] = gr.update(value=topbar.render_topbar(target.LABEL, target.ADMIN_ONLY, user))
            return updates

        def show_page(page_name, user):
            """Cập nhật visibility toàn bộ trang, trạng thái active của sidebar, tiêu đề và breadcrumb."""
            return page_updates(page_name, user)

        nav_outputs = [*page_cols.values(), *nav_btns.values(), top]

        def make_show(page_name):
            def _show(user):
                return show_page(page_name, user)

            return _show

        def wire_navigation(button, page_name):
            event = button.click(make_show(page_name), inputs=[session], outputs=nav_outputs)
            parts = page_parts.get(page_name, {})
            if "load_fn" in parts:  # nạp dữ liệu SAU khi show_page đã kiểm tra quyền
                event.then(parts["load_fn"], inputs=[session], outputs=parts["load_outputs"])

        for name, btn in nav_btns.items():
            wire_navigation(btn, name)

        def refresh_user_card(user):
            return render.sidebar_user_html(user) if user is not None else ""

        for parts in page_parts.values():
            if "after_save" in parts:  # trang sửa hồ sơ: họ tên mới hiện ngay ở góc phải đầu trang
                parts["after_save"].then(refresh_user_card, inputs=[session], outputs=[user_card])
            for key, comp in parts.items():
                if key.startswith("goto_") and comp is not None:
                    target_name = next(n for n in by_name if key == f"goto_{n}" or key.startswith(f"goto_{n}_"))
                    wire_navigation(comp, target_name)

        # ---- vào ứng dụng sau đăng nhập / vào thử ----
        enter_outputs = [auth_view, app_view, admin_group, user_card, top, *auth["forms"], *page_cols.values(), *nav_btns.values()]

        def enter_app(user):
            if user is None:
                return {auth_view: gr.update(visible=True), app_view: gr.update(visible=False)}
            updates = page_updates(DEFAULT_PAGE, user)
            updates.update(
                {
                    auth_view: gr.update(visible=False),
                    app_view: gr.update(visible=True),
                    admin_group: gr.update(visible=user.is_admin),
                    user_card: gr.update(value=render.sidebar_user_html(user)),
                }
            )
            updates.update({field: gr.update(value="") for field in auth["forms"]})  # xóa mật khẩu khỏi form
            return updates

        auth["login_btn"].click(login.handle_login, inputs=[auth["login_user"], auth["login_pass"], auth["remember"]], outputs=[session, auth["login_msg"]]).then(
            enter_app, inputs=[session], outputs=enter_outputs
        )
        auth["login_pass"].submit(login.handle_login, inputs=[auth["login_user"], auth["login_pass"], auth["remember"]], outputs=[session, auth["login_msg"]]).then(
            enter_app, inputs=[session], outputs=enter_outputs
        )
        if auth["dev_user"] is not None:  # chỉ tồn tại khi DEV_BYPASS_LOGIN=1; handler còn kiểm tra lại cờ ở server
            auth["dev_user"].click(login.handle_dev_user, outputs=[session, auth["login_msg"]]).then(enter_app, inputs=[session], outputs=enter_outputs)
            auth["dev_admin"].click(login.handle_dev_admin, outputs=[session, auth["login_msg"]]).then(enter_app, inputs=[session], outputs=enter_outputs)

        # ---- đăng xuất ----
        def on_logout(user):
            if user is not None:
                try:
                    auth_service.logout(user)
                except Exception:
                    logging.getLogger(__name__).exception("Không ghi được nhật ký đăng xuất")  # đăng xuất vẫn phải thành công
            return {
                session: None,
                auth_view: gr.update(visible=True),
                app_view: gr.update(visible=False),
                admin_group: gr.update(visible=False),
                user_card: gr.update(value=""),
                top: gr.update(value=""),
            }

        side["logout"].click(on_logout, inputs=[session], outputs=[session, auth_view, app_view, admin_group, user_card, top])

    return demo
