# Truy vết đề cương → skeleton → báo cáo

Nguồn: đề cương chi tiết CNTT-KLCN311 (mục *Mục tiêu*, *Các nội dung cụ thể cần thực hiện*, *Thang điểm*, *Thời gian và các công việc trong tuần*) và báo cáo `KLCN311_BaoCaoTongHop.docx`. Trạng thái lấy từ "TRẠNG THÁI HIỆN TẠI" của dự án (cập nhật theo tiến độ nhóm, không suy diễn thêm).

Ký hiệu: **Hoàn thành** / **Một phần** / **Chưa làm**.

## A. Mục tiêu nghiên cứu và ứng dụng (a–f)

| # | Mục tiêu (đề cương) | Module skeleton | Mục báo cáo | Trạng thái |
|---|---|---|---|---|
| a | Khảo sát SER 5 năm gần đây (CNN, LSTM, Transformer: Wav2Vec2, HuBERT) | — (tài liệu) | Chương 1: 1.1, 1.3 | **Hoàn thành** |
| b | Tiền xử lý tín hiệu, trích xuất đặc trưng (MFCC, spectrogram, pitch, energy) | `ml/preprocess.py`, `services/preprocessing_service.py` | Chương 3 (3.1 tiền xử lý, 3.2 đặc trưng 212 chiều, 3.3 DataLoader/cache) | **Hoàn thành** ở nghiên cứu; port vào skeleton: chưa |
| c | Transformer nhẹ (Knowledge Distillation hoặc Pruning), giảm tham số, tăng tốc | `ml/model.py`, `ml/inference.py` | 2.5, 4.3 (DistilHuBERT + LoRA: 73,33% / 71,21%) | **Một phần**: fine-tune xong; chưa Pruning; chưa đo HuBERT/wav2vec 2.0 gốc |
| d | XAI: Attention Visualization / Heatmap / Weights | `ml/xai.py`, `services/xai_service.py` | 5.2 (Hình 5.1) | **Một phần**: heatmap trên dạng sóng có; trên spectrogram chưa; Captum (tùy chọn) chưa |
| e | Thực nghiệm so sánh Accuracy, F1, thời gian suy luận, kích thước trước/sau cải tiến | `ml/evaluate.py`, `ml/benchmark.py`, `assets/metrics/*.json`, trang Mô hình & hiệu năng | 4.2, 5.1 (Bảng 5.1–5.4) | **Một phần**: chưa đo HuBERT/wav2vec 2.0 gốc, chưa Pruning, độ trễ đo chưa đồng nhất; kiểm thử chéo TESS/CREMA-D chưa làm |
| f | Ứng dụng demo: upload âm thanh, dự đoán cảm xúc kèm giải thích trực quan | `app.py`, `ui/`, `services/` | 5.3 (nội dung 5.3.1–5.3.2 hiện còn trống) | **Chưa làm** (có skeleton chạy được với dữ liệu mẫu) |

## B. Thang điểm (mục 6 đề cương) → module → báo cáo

| STT | Nội dung thang điểm (CLO) | Module skeleton | Mục báo cáo | Trạng thái |
|---|---|---|---|---|
| 1 | Khảo sát nghiệp vụ; lý do chọn đề tài, mục tiêu; tình hình SER 5 năm; phương pháp, dataset, kỹ thuật tối ưu & giải thích (CLO1.1) | — | Chương 1 | Hoàn thành |
| 2 | Lập kế hoạch và phân công (CLO6) | `docs/roadmap.md`, `CONTRIBUTING.md` | (ngoài báo cáo) | Một phần (roadmap tuần 9–12 mới được viết) |
| 3 | Xác định bài toán; nghiên cứu liên quan; ưu nhược điểm (CLO1.2) | — | 1.1, 1.3, 1.4 | Hoàn thành |
| 4a | Sơ đồ Use-Case nghiệp vụ và đặc tả (CLO2.1) | `docs/use-cases.md` | 2.2 (Bảng 2.2–2.9) | Hoàn thành |
| 4b | **Sơ đồ lớp thiết kế** (CLO2.1) | `docs/class-diagram.md` (dựng từ `models/`, `services/`) | **báo cáo chưa có** | Một phần (có Mermaid trong docs, chưa vào báo cáo) |
| 4c | Mô hình dữ liệu (CLO2.1) | `models/`, `docs/database.md` | 2.4 (+ 2 bảng bổ sung chưa có trong báo cáo) | Hoàn thành (cần cập nhật 2 bảng) |
| 4d | Thiết kế giao diện (CLO2.2) | `stitch/`, `docs/ui-pages.md`, `docs/stitch-mapping.md` | (chưa có mục riêng) | Một phần |
| 4e | Mô hình hóa thuật toán (CLO2.2) | `ml/model.py` | 2.5 (Hình 2.5, 2.6) | Hoàn thành |
| 5 | Mô tả thuật toán: khái niệm Transformer & SER; vấn đề tồn tại mà cải tiến giải quyết (tốc độ, dung lượng, XAI) (CLO1.1) | `ml/model.py` | 1.3.3, 2.5, 5.1 | Hoàn thành |
| 6a | Xác thực người dùng: đăng ký, đăng nhập, đăng xuất, **quên mật khẩu**, phân quyền (CLO3) | `services/auth_service.py`, `core/security.py`, `core/session.py`, `ui/pages/login.py` | 2.2 UC01; 5.3 | **Chưa làm** |
| 6b | Upload WAV/MP3 + kiểm tra hợp lệ | `services/audio_service.py`, `ui/pages/analyze.py` | UC02; 5.3.2 | Chưa làm |
| 6c | Thu âm trực tiếp trên web | `ui/pages/analyze.py` (tab Thu âm) | UC02; 5.3.2 | Chưa làm |
| 6d | Tiền xử lý tự động | `ml/preprocess.py`, `services/preprocessing_service.py` | 3.1; UC03/UC07 | Một phần (logic gốc xong ở `ser_project`, chưa port) |
| 6e | Danh sách mẫu âm thanh: trình phát, lọc, tìm kiếm | `services/history_service.py::list_audio_samples`, `ui/pages/admin_audio.py` | (chưa có mục) | Chưa làm |
| 6f | Danh sách lịch sử phân tích | `services/history_service.py`, `ui/pages/history.py` | UC05 | Chưa làm |
| 6g | Xem chi tiết kết quả + biểu đồ XAI | `ui/pages/history.py` (drawer), `ml/xai.py` | UC04, UC05; 5.2 | Một phần (XAI dạng sóng đã có ở notebook) |
| 6h | Cài đặt và huấn luyện mô hình Transformer cải tiến (Distillation/LoRA/XAI) | `ml/` | 4.3 | Hoàn thành (huấn luyện); chưa port |
| 6i | Tích hợp dự đoán + XAI vào ứng dụng web | `services/inference_service.py`, `ui/pages/analyze.py` | 5.3 | Chưa làm |
| 6j | Quản trị: quản lý dữ liệu và mô hình, theo dõi hiệu suất hệ thống | `ui/pages/admin_*.py`, `services/admin_service.py` | UC06 (Bảng 2.8) | Một phần (báo cáo UC06 chỉ có người dùng/nhật ký/trạng thái; **thiếu quản lý dữ liệu và mô hình**) |
| — | Kiểm thử và triển khai hệ thống (CLO4) | `tests/`, `docs/test-plan.md`, `docs/deployment.md` | Chương 5 (5.3) | Chưa làm |
| 7–10 | Nội dung/hình thức báo cáo; thái độ; phong cách báo cáo, slide (CLO5.1, CLO6, CLO5.2) | — | Toàn báo cáo | Báo cáo chương 1–5 xong, mục 5.3 còn trống |
| 11 | Điểm khuyến khích NCKH | — | — | — |

> Điểm số từng dòng con lấy từ bảng gốc trong đề cương; bảng chỉ truy vết nội dung, không lặp lại số điểm vì bản trích văn bản của bảng gốc bị lẫn ô.

## C. Yêu cầu tuần 9–12 → việc cần làm

Xem `docs/roadmap.md`.

## D. Dataset

| Dataset (đề cương) | Trạng thái | Module |
|---|---|---|
| RAVDESS | Đã dùng (tách 18–3–3 diễn viên, Test 180 mẫu) | `ml/datasets.py` (label map) |
| CREMA-D (6 nhãn) | Chưa làm (kiểm thử chéo) | `ml/datasets.py` (stub) |
| TESS | Chưa làm (kiểm thử chéo) | `ml/datasets.py` (stub) |
| Tiếng Việt (VLSP hoặc tự thu âm, mở rộng) | Chưa làm | ghi chú trong `ml/datasets.py` |

## E. Điểm lệch cần người quyết định

| Vấn đề | Chi tiết | Đề xuất |
|---|---|---|
| UC03 và UC07 trùng nhau | Báo cáo Bảng 2.2/2.5/2.9: cả hai là "tiền xử lý tự động"; tiền điều kiện UC07 lại ghi "thu âm từ UC03" | Gộp thành một UC hoặc tách UC03 = thu âm; sửa lại báo cáo |
| Quên mật khẩu | Đề cương tuần 9 yêu cầu; báo cáo (UC01, Bảng 2.3 — chỉ "Đăng ký và đăng nhập") và Stitch chưa có; cần bảng `password_resets` | Giữ; bổ sung vào UC01 và Mục 2.4 của báo cáo; chọn cách gửi mã (hiển thị trên UI cho demo / SMTP) |
| 2 trang admin chưa có Stitch | "Quản lý mô hình AI", "Quản lý dữ liệu âm thanh" (đề cương: "Quản lý dữ liệu và mô hình"); UC06 báo cáo chưa nêu | Giữ sau cờ `ENABLE_ADMIN_EXTRA_PAGES`; thiết kế Stitch hoặc bỏ |
| 2 bảng DB bổ sung | `system_logs`, `password_resets` chưa có trong Mục 2.4 | Cập nhật báo cáo |
| Số liệu Bi-LSTM | F1: 32,80 (Bảng 5.1) vs 33,37 (Bảng 4.6); lần chạy chính 38,33 / 37,05; độ trễ 0,02 vs 0,01 ms | Chốt một lần chạy và đồng bộ mọi bảng |
| Độ trễ 1D-CNN | 4,16 ms (Bảng 5.4) vs 1,19 ms (Bảng 4.6) | Đo lại bằng `ml/benchmark.py` |
| Stitch trang admin gộp | Stitch chỉ có 1 trang admin; yêu cầu dự án là 3 trang | Đã tách 3 trang |
| Stitch tự đặt số liệu mô hình | HuBERT 74,10%, wav2vec 2.0 71,80%, SVM 54,80%… | Không dùng; chỉ dùng số trong báo cáo |
| Báo cáo Mục 5.3 | 5.3.1 (kiến trúc Gradio) và 5.3.2 (hướng dẫn vận hành) đang trống | Viết sau khi app chạy |
