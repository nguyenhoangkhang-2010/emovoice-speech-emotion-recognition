# UC06: trạng thái dịch vụ (DB, kho tệp, mô hình đã nạp) cho hàng trạng thái ở admin Tổng quan.
from core.session import SessionUser


def get_system_status(session: SessionUser):
    raise NotImplementedError(
        "TODO UC06: kiểm tra kết nối DB, thư mục storage ghi được, mô hình đã nạp + độ trễ gần nhất; require_admin. "
        "Khung Stitch hiện API Gateway/NGINX, GPU T4, PostgreSQL — không có trong kiến trúc Gradio, thay bằng 3 dịch vụ thật: Ứng dụng Gradio, Mô hình AI, Cơ sở dữ liệu"
    )
