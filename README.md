# EmoVoice

Ứng dụng web nhận diện cảm xúc qua giọng nói tiếng Việt (SER) bằng **Gradio**, kèm giải thích XAI (Attention Heatmap). Đề tài CNTT-KLCN311 "Cải tiến thuật toán nhận diện cảm xúc qua giọng nói (SER) bằng transformer".

> **Đây là skeleton.** `python app.py` chạy được và hiển thị toàn bộ khung giao diện theo Stitch với dữ liệu mẫu cứng; logic nghiệp vụ (`services/`) và mô hình (`ml/`) mới chỉ là chữ ký hàm kèm TODO. Code ML gốc nằm ở `ser_project/` (không sửa), sẽ được port dần.

## Chức năng (theo đề cương)

- Người dùng cuối: đăng ký, đăng nhập, đăng xuất, **quên mật khẩu**; tải WAV/MP3 (có kiểm tra hợp lệ) hoặc **thu âm trực tiếp**; tiền xử lý tự động (16 kHz mono, cắt lặng `top_db=25`, chuẩn hóa [-1, 1], cố định 3 s = 48.000 mẫu); kết quả 8 cảm xúc kèm độ tin cậy và biểu đồ XAI; lịch sử phân tích, danh sách mẫu âm thanh (lọc, tìm kiếm); trang Mô hình & hiệu năng.
- Quản trị viên: tổng quan, quản lý người dùng, nhật ký hệ thống; (tùy chọn) quản lý mô hình AI, quản lý dữ liệu âm thanh.
- Yêu cầu phi chức năng: tiền xử lý + suy luận < 1,5 s cho đoạn 3 s; mật khẩu băm; cảnh báo "độ tin cậy thấp" khi mọi xác suất < 30%.

## Mô hình

`ntu-spml/distilhubert` (đóng băng) + LoRA (r=8, alpha=16, dropout=0,1, gắn `q_proj`/`v_proj`) + Temporal Attention Pooling (Linear 768→1, softmax theo thời gian, 149 khung / 3 s) + head 768→256→GELU→LayerNorm→Dropout(0,3)→8. `forward` trả `(logits, attn_weights)`; checkpoint `best_distilhubert_lora.pt` (`state_dict`).

8 nhãn: 0 neutral/Trung tính, 1 calm/Êm đềm, 2 happy/Vui vẻ, 3 sad/Buồn bã, 4 angry/Tức giận, 5 fearful/Sợ hãi, 6 disgust/Chán ghét, 7 surprised/Ngạc nhiên.

Kết quả (báo cáo, RAVDESS Actor 22–24, Test độc lập 180 mẫu): Accuracy 73,33%, Macro F1 71,21%, 249.353 / 23.741.321 tham số huấn luyện (1,05%), 90,6 MiB, 7,60 ms/mẫu (GPU). Số liệu đầy đủ ở `assets/metrics/`.

## Chạy thử

```powershell
cd emovoice
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt            # chưa ghim phiên bản; gradio>=5 (cả 5 và 6 đều được hỗ trợ)
Copy-Item .env.example .env
# DEV_BYPASS_LOGIN=1 trong .env để có nút "Vào thử (Người dùng/Quản trị viên)" xem giao diện
python app.py                              # http://127.0.0.1:7860
```

Chi tiết (local, Colab, Hugging Face Spaces): [docs/deployment.md](docs/deployment.md).

## Cấu trúc

```
emovoice/
  app.py                 điểm vào duy nhất (Gradio)
  core/                  config, security, session (SessionUser, require_login, require_admin), logging
  db/                    base, session, init_db, seed
  models/                9 bảng SQLAlchemy (7 bảng báo cáo + system_logs + password_resets)
  services/              auth, audio, preprocessing, inference, xai, history, model, admin, system_status
  ml/                    config, preprocess, model, inference, xai, datasets, evaluate, benchmark, weights/
  ui/                    layout, render, theme, i18n_vi, css/, templates/, components/, pages/
  assets/metrics/        model_metrics.json, confusion_matrix_*.json (UI chỉ đọc)
  stitch/                bản sao nguyên bản file Stitch (images/, html/, DESIGN.md)
  storage/ logs/         uploads, heatmaps, mel / nhật ký (chỉ giữ .gitkeep)
  tests/                 pytest (phần lớn skip kèm TODO)
  docs/                  tài liệu thiết kế (bảng dưới)
  _archive_old_skeleton/ skeleton FastAPI/React cũ (lưu trữ, không xóa)
```

## Tài liệu

| File | Nội dung |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Kiến trúc Gradio, DFD mức 0/1, luồng phân tích |
| [docs/use-cases.md](docs/use-cases.md) | UC01–UC07 → service → trang |
| [docs/database.md](docs/database.md) | 9 bảng, ER, 2 bảng bổ sung |
| [docs/class-diagram.md](docs/class-diagram.md) | Sơ đồ lớp thiết kế (Mermaid) |
| [docs/ui-pages.md](docs/ui-pages.md) | Các trang, phân quyền, chỗ Gradio khác Stitch |
| [docs/stitch-mapping.md](docs/stitch-mapping.md) | Stitch → module → component; token; kiểm tra đen/gradient |
| [docs/outline-traceability.md](docs/outline-traceability.md) | Đề cương (mục tiêu a–f, thang điểm) → module → báo cáo → trạng thái |
| [docs/test-plan.md](docs/test-plan.md) | Ca kiểm thử UC01–UC07 |
| [docs/deployment.md](docs/deployment.md) | Local, Colab, Hugging Face Spaces |
| [docs/roadmap.md](docs/roadmap.md) | Tuần 9–12 và thứ tự việc tiếp theo |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Quy ước nhánh, commit, chia việc |

## Cấu hình (`.env`)

`DATABASE_URL`, `SECRET_KEY`, `MAX_UPLOAD_MB=10`, `ALLOWED_AUDIO=wav,mp3`, `LOW_CONFIDENCE_THRESHOLD=0.30`, `MODEL_CHECKPOINT_PATH`, `PASSWORD_RESET_TTL_MINUTES=15`, `DEV_BYPASS_LOGIN=0`, `ENABLE_ADMIN_EXTRA_PAGES=0`, `SERVER_PORT`, tài khoản admin mặc định (`ADMIN_*`). Xem `.env.example`.
