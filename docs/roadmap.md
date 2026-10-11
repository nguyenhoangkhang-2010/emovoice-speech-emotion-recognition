# Lộ trình (đề cương: tuần 9–12)

Nguồn: mục *Thời gian và các công việc trong tuần* của đề cương. Đề cương yêu cầu nhóm gặp GVHD ít nhất 1 lần/tuần và **tích hợp phần việc đã phân công vào một tài liệu/phần mềm chung trước mỗi buổi báo cáo** (xem `CONTRIBUTING.md`).

| Tuần | Nội dung theo đề cương | Việc cần làm trong repo | Module |
|---|---|---|---|
| 9 | Tích hợp module giải thích (Attention Visualization trên spectrogram hoặc Attention Heatmap); xây dựng ứng dụng (đăng ký, đăng nhập, **quên mật khẩu**, upload âm thanh, dự đoán, hiển thị kết quả) | Port `ml/` từ `ser_project`; cài `auth_service` (+ quên mật khẩu), `audio_service`, `preprocessing_service`, `inference_service`, `xai_service`; nối trang Đăng nhập và Phân tích mới với service thật; `render_attention_on_mel` | `ml/`, `services/`, `ui/pages/login.py`, `analyze.py` |
| 10 | Hoàn thiện ứng dụng demo: hiển thị giải thích trực quan kèm kết quả; tích hợp lưu lịch sử dự đoán | `history_service` + trang Lịch sử (lọc, tìm, phân trang, drawer, trình phát); lưu `predictions`/`prediction_scores`; trang Mô hình & hiệu năng đọc `evaluate`/`benchmark` | `services/history_service.py`, `ui/pages/history.py`, `model_performance.py` |
| 11 | Hoàn chỉnh ứng dụng; kiểm thử toàn diện hệ thống | Ba trang admin (+ 2 trang quản lý mô hình/dữ liệu nếu chốt giữ); benchmark trước/sau cải tiến; kiểm thử chéo TESS/CREMA-D; viết test theo `test-plan.md`; sửa lỗi | `services/admin_service.py`, `ui/pages/admin_*.py`, `ml/benchmark.py`, `ml/datasets.py`, `tests/` |
| 12 | Hoàn chỉnh báo cáo; thiết kế báo cáo PowerPoint; nộp báo cáo | Viết Mục 5.3 (kiến trúc Gradio, hướng dẫn vận hành), sơ đồ lớp, cập nhật Mục 2.4 (2 bảng bổ sung) và UC (quên mật khẩu, quản trị dữ liệu/mô hình); chốt số liệu Bi-LSTM; `deployment.md` | `docs/`, báo cáo |

## Thứ tự nên làm tiếp

1. **`ml/` port từ `ser_project`**: `preprocess.py`, `model.py`, `inference.py`, `xai.py` (giữ tên hàm hiện có: `load_and_preprocess_audio`, `pad_or_truncate_waveform`, `TemporalAttentionPooling`, `DistilHuBERTForSER`); test `test_preprocess.py`, `test_inference.py`.
2. **Đăng nhập + DB + quên mật khẩu**: `db/seed.py`, `core/security.py`, `auth_service`; test `test_auth.py`, `test_password_reset.py`.
3. **Luồng Phân tích mới**: `audio_service` → `preprocessing_service` → `inference_service` → `xai_service`; thay kết quả mẫu cứng trong `analyze.py`.
4. **Lịch sử**: `history_service`, bỏ dữ liệu mẫu trong `history.py`; test `test_history_filter.py`.
5. **Mô hình & hiệu năng** đọc từ `evaluate` / `benchmark` (xuất JSON thật vào `assets/metrics/`).
6. **Ba trang admin** (+ trang tùy chọn): `admin_service`, `system_status_service`; test `test_admin_access.py`.
7. **Benchmark trước/sau cải tiến + kiểm thử chéo TESS/CREMA-D** (`ml/benchmark.py`, `ml/datasets.py`); cân nhắc Pruning, XAI trên Mel, Captum (tùy chọn).
8. **`test-plan.md` và `deployment.md`**: chạy các ca kiểm thử, triển khai Colab/Spaces, ghi số liệu thật (CPU/GPU).

## Mở rộng (nếu còn thời gian)

- Dataset tiếng Việt (VLSP hoặc tự thu âm nhỏ) — đề cương ghi "mở rộng".
- Captum cho XAI (tùy chọn theo đề cương; chưa thêm vào `requirements.txt`).
- Pruning, lượng tử hóa, gộp LoRA vào trọng số gốc để giảm độ trễ.
