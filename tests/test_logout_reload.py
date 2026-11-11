# Đăng xuất phải bỏ sạch trạng thái trên trình duyệt: Gradio giữ giá trị thành phần theo trình duyệt chứ không theo tài khoản,
# nên nếu chỉ ẩn khung ứng dụng thì người đăng nhập sau thấy lại kết quả phân tích của người trước.
from ui.layout import build_app


def test_logout_reloads_the_page_so_the_next_user_starts_clean():
    demo = build_app()
    logout = next(i for i, f in demo.fns.items() if getattr(f.fn, "__name__", "") == "on_logout")
    followers = [f for f in demo.fns.values() if f.trigger_after == logout]
    assert any(f.js and "location.reload" in f.js for f in followers)
