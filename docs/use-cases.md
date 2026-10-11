# Use case → service → trang UI (Gradio)

Vai trò: **User** (người dùng cuối), **Admin** (quản trị viên: thấy toàn bộ trang user + nhóm "Quản trị hệ thống"). Tên UC theo báo cáo Bảng 2.2–2.9.

| UC | Tên (báo cáo) | Vai trò | Service (hàm) | Trang UI / module |
|---|---|---|---|---|
| UC01 | Đăng ký và đăng nhập tài khoản (+ đăng xuất, **quên mật khẩu** theo đề cương tuần 9) | Khách | `auth_service.register`, `login`, `logout`, `request_password_reset`, `reset_password` | Đăng nhập — `ui/pages/login.py` (tab Đăng nhập \| Đăng ký + panel Quên mật khẩu) |
| UC02 | Tải tệp âm thanh hoặc thu âm trực tiếp | User, Admin | `audio_service.validate_upload`, `save_upload` | Phân tích mới, trạng thái 1 — `ui/pages/analyze.py` |
| UC03 | Tiền xử lý âm thanh tự động (nạp, 16 kHz mono, cắt lặng `top_db=25`) | Hệ thống | `preprocessing_service.preprocess_audio` | Phân tích mới, trạng thái 2 (đang xử lý) |
| UC04 | Phân tích cảm xúc và hiển thị XAI | User, Admin | `inference_service.run_inference`, `is_low_confidence`, `save_prediction`; `xai_service.build_waveform_heatmap`, `build_mel_attention` | Phân tích mới, trạng thái 3 (kết quả) |
| UC05 | Tra cứu lịch sử phân tích (+ danh sách mẫu âm thanh có lọc/tìm kiếm) | User, Admin | `history_service.list_history`, `get_history_detail`, `list_audio_samples` | Lịch sử phân tích + drawer chi tiết — `ui/pages/history.py` |
| UC06 | Quản lý người dùng và hệ thống | Admin | `admin_service.*`, `system_status_service.get_system_status`, `model_service.*` | Tổng quan, Quản lý người dùng, Nhật ký hệ thống; (tùy chọn) Quản lý mô hình AI, Quản lý dữ liệu âm thanh |
| UC07 | Tiền xử lý âm thanh tự động (tiến trình ngầm: chuẩn hóa biên độ [-1, 1], cố định 3 s = 48.000 mẫu) | Hệ thống | `preprocessing_service.preprocess_audio` (cùng pipeline UC03) | Phân tích mới, trạng thái 2 |

> Báo cáo tự mâu thuẫn: Bảng 2.2 liệt kê UC03 "Tiền xử lý âm thanh tự động" và UC07 "Tiền xử lý tự động (Tiến trình ngầm)" với mô tả gần như trùng nhau, trong khi tiền điều kiện của UC07 (Bảng 2.9) lại viết "thu âm từ UC03". Giả định dùng ở đây: UC03 = nạp + resample + cắt lặng, UC07 = chuẩn hóa biên độ + cố định độ dài, cả hai nằm trong cùng một hàm pipeline. **Cần người quyết định** gộp UC03/UC07 hoặc tách rõ; đồng thời báo cáo chưa có UC đăng xuất/quên mật khẩu (đề cương tuần 9 yêu cầu) và UC06 chưa có quản lý dữ liệu/mô hình.

Trang ngoài UC: **Mô hình & hiệu năng** dùng `model_service.load_metrics`, `load_confusion_matrix` (đọc `assets/metrics/*.json`).

## Quy tắc nghiệp vụ chung

- Mọi trang trong `view-app` yêu cầu `SessionUser` (`require_login`); trang và handler admin yêu cầu `require_admin`.
- Người dùng chỉ truy cập `audio_files` / `predictions` của chính mình; Admin xem được mẫu âm thanh của mọi người dùng ở trang "Quản lý dữ liệu âm thanh".
- Tài khoản `is_active = false` không đăng nhập được.
- Thu âm micro do `gr.Audio(sources=["microphone"])` ghi ra tệp; `audio_service` vẫn kiểm tra định dạng/dung lượng như tệp tải lên.
- Quên mật khẩu: mã đặt lại hết hạn sau `PASSWORD_RESET_TTL_MINUTES` (15 phút), dùng một lần; chưa có SMTP nên bản demo hiển thị mã trên giao diện (cần người quyết định, xem `outline-traceability.md`).
