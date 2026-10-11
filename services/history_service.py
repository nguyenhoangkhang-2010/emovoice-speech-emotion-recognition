# UC05 (báo cáo Bảng 2.7): lịch sử phân tích + danh sách mẫu âm thanh có lọc/tìm kiếm (đề cương thang điểm mục 6).
from typing import Optional

from core.session import SessionUser


def list_history(session: SessionUser, page: int = 1, page_size: int = 10, emotion: Optional[str] = None, days: Optional[int] = None, q: Optional[str] = None):
    raise NotImplementedError("TODO UC05: lọc theo user_id, cảm xúc, khoảng ngày, q (tên tệp); trả (hàng, tổng) đã phân trang")


def get_history_detail(session: SessionUser, prediction_id: int):
    raise NotImplementedError("TODO UC05: chi tiết một lượt (8 xác suất, heatmap_path, audio) — 404 nếu không thuộc user")


def list_audio_samples(session: SessionUser, q: Optional[str] = None, emotion: Optional[str] = None):
    raise NotImplementedError("TODO (đề cương thang điểm mục 6): danh sách mẫu âm thanh của user với trình phát, lọc, tìm kiếm")
