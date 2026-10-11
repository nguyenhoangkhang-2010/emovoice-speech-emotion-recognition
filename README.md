# EmoVoice

Ứng dụng web nhận diện cảm xúc qua giọng nói (Speech Emotion Recognition - SER) xây bằng **Gradio**, dùng mô hình **DistilHuBERT + LoRA + Temporal Attention Pooling** và giải thích quyết định bằng biểu đồ chú ý (XAI).
Đề tài khóa luận CNTT-KLCN311: *Cải tiến thuật toán nhận diện cảm xúc qua giọng nói (SER) bằng transformer*.

> **Trạng thái hiện tại: skeleton có giao diện chạy được.** `python app.py` hiển thị đầy đủ khung giao diện theo thiết kế Stitch với dữ liệu mẫu. Đăng nhập thật, lưu CSDL và suy luận bằng mô hình thật còn là phần việc tiếp theo (các hàm trong `services/` và `ml/` mới là chữ ký kèm TODO). Để xem giao diện, dùng nút **Vào thử** (xem mục 4).

## 1. Tính năng

| Nhóm | Nội dung |
|---|---|
| Công khai | Đăng nhập, Đăng ký, Quên mật khẩu; trang **Giới thiệu**; trang **Hướng dẫn** |
| Người dùng | Phân tích mới (tải WAV/MP3 hoặc thu âm, tiền xử lý tự động, 8 cảm xúc + độ tin cậy + biểu đồ chú ý), Lịch sử phân tích, Mô hình & hiệu năng |
| Quản trị viên | Toàn bộ chức năng của người dùng, cộng thêm: Tổng quan, Quản lý người dùng, Nhật ký hệ thống (tùy chọn: Quản lý mô hình AI, Quản lý dữ liệu âm thanh) |

Người dùng thường không thấy và không gọi được các trang quản trị: sidebar chỉ dựng nhóm quản trị cho Admin và mọi handler admin đều kiểm tra vai trò ở phía server.

8 nhãn cảm xúc: neutral (Trung tính), calm (Êm đềm), happy (Vui vẻ), sad (Buồn bã), angry (Tức giận), fearful (Sợ hãi), disgust (Chán ghét), surprised (Ngạc nhiên).

## 2. Yêu cầu

- Python **3.10 – 3.12** (khuyên dùng 3.11; bản đã thử: Python 3.11, Gradio 6.30).
- Cần Internet khi mở giao diện để tải font và icon từ Google Fonts. Nếu offline, icon sẽ hiện thành chữ (ví dụ `mic`, `check`).
- GPU NVIDIA là tùy chọn, chỉ cần khi chạy mô hình thật; CPU vẫn chạy được nhưng chậm hơn.

## 3. Cài đặt

Lấy mã nguồn rồi vào thư mục dự án:

```bash
git clone <địa-chỉ-repo>
cd emovoice
```

Chọn **một** trong hai cách tạo môi trường.

### Cách A – Anaconda

Mở **Anaconda Prompt** (hoặc terminal đã chạy `conda init`):

```bash
conda create -n emovoice python=3.11 -y
conda activate emovoice
```

### Cách B – `.venv`

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Nếu PowerShell chặn script, chạy một lần: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

Windows (cmd): `.venv\Scripts\activate.bat`

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Cài thư viện (dùng chung cho cả hai cách)

Chỉ để **xem giao diện** (nhẹ, nhanh):

```bash
pip install gradio sqlalchemy python-dotenv bcrypt pandas plotly matplotlib seaborn
```

Để **chạy mô hình thật** (nặng, có torch):

```bash
pip install -r requirements.txt
pip install --upgrade "torchao>=0.16.0"
```

Ghi chú về `torch`: nếu có card NVIDIA, bạn nên cài bản CUDA theo hướng dẫn trên trang chủ PyTorch (chọn Pip và phiên bản CUDA) **trước** khi chạy `pip install -r requirements.txt`, để tránh phải gỡ cài lại. `peft` cần `torchao>=0.16` (sự cố đã gặp ở Mục 4.1.1 của báo cáo).

### Tạo file cấu hình

- PowerShell: `Copy-Item .env.example .env`
- Anaconda Prompt hoặc cmd: `copy .env.example .env`
- macOS / Linux: `cp .env.example .env`

## 4. Chạy ứng dụng

Mở file `.env` và đặt `DEV_BYPASS_LOGIN=1` để có hai nút **Vào thử (Người dùng)** và **Vào thử (Quản trị viên)** ở trang đăng nhập, rồi chạy:

```bash
python app.py
```

Mở trình duyệt tại <http://127.0.0.1:7860> (đổi cổng bằng `SERVER_PORT` trong `.env`).

Lưu ý:
- Khi triển khai thật, đặt `DEV_BYPASS_LOGIN=0` (nút Vào thử sẽ biến mất và server từ chối cả khi bị gọi trực tiếp).
- Thanh trên cùng của trang đăng nhập có ba nút: **Giới thiệu**, **Hướng dẫn** (hai trang công khai) và **Đăng nhập** (quay lại form đăng nhập).
- Muốn xem hai trang admin chưa có thiết kế Stitch, đặt `ENABLE_ADMIN_EXTRA_PAGES=1`.

## 5. Kiểm thử

```bash
pytest
```

Phần lớn test đang ở trạng thái `skip` kèm TODO; chỉ có test kiểm tra quyền admin chạy thật.

## 6. Mô hình

`ntu-spml/distilhubert` (đóng băng) + LoRA (r=8, alpha=16, dropout=0,1, gắn vào `q_proj` và `v_proj`) + Temporal Attention Pooling (Linear 768→1, softmax theo thời gian, 149 khung cho 3 giây) + đầu phân loại 768→256→GELU→LayerNorm→Dropout(0,3)→8. Hàm `forward` trả về `(logits, attn_weights)`. Checkpoint `best_distilhubert_lora.pt` (là `state_dict`) đặt trong `ml/weights/` (đã nằm trong `.gitignore`).

Kết quả trong báo cáo (RAVDESS, diễn viên 22–24, tập Test độc lập 180 mẫu): Accuracy 73,33%, Macro F1 71,21%, huấn luyện 249.353 / 23.741.321 tham số (1,05%), checkpoint 90,6 MiB, độ trễ 7,60 ms/mẫu (GPU). Số liệu đầy đủ nằm ở `assets/metrics/`; giao diện đọc số từ đó chứ không viết cứng.

Lưu ý: mô hình huấn luyện trên RAVDESS (giọng diễn xuất tiếng Anh), nên với giọng tự nhiên hoặc tiếng Việt kết quả có thể kém hơn.

## 7. Cấu trúc thư mục

```text
emovoice/
  app.py                 điểm vào duy nhất (Gradio)
  core/                  config, security, session (SessionUser, require_login, require_admin), logging
  db/                    base, session, init_db, seed
  models/                9 bảng SQLAlchemy (7 bảng của báo cáo + system_logs + password_resets)
  services/              auth, audio, preprocessing, inference, xai, history, model, admin, system_status
  ml/                    config, preprocess, model, inference, xai, datasets, evaluate, benchmark, weights/
  ui/                    layout, render, theme, i18n_vi, css/, templates/, components/, pages/
  assets/metrics/        model_metrics.json, confusion_matrix_*.json (giao diện chỉ đọc)
  stitch/                bản sao nguyên bản thiết kế Stitch (images/, html/, DESIGN.md)
  storage/  logs/        tệp tải lên, heatmap, mel / nhật ký (chỉ giữ .gitkeep)
  tests/                 pytest
  docs/                  tài liệu thiết kế
  _archive_old_skeleton/ skeleton FastAPI/React cũ (lưu trữ, không dùng nữa)
```

## 8. Tài liệu

| File | Nội dung |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Kiến trúc Gradio, DFD mức 0/1, luồng phân tích |
| [docs/use-cases.md](docs/use-cases.md) | UC01–UC07 → service → trang |
| [docs/database.md](docs/database.md) | 9 bảng, quan hệ, 2 bảng bổ sung |
| [docs/class-diagram.md](docs/class-diagram.md) | Sơ đồ lớp thiết kế (Mermaid) |
| [docs/ui-pages.md](docs/ui-pages.md) | Các trang, phân quyền, chỗ Gradio khác Stitch |
| [docs/stitch-mapping.md](docs/stitch-mapping.md) | Stitch → module → component; token màu; kiểm tra màu đen/gradient |
| [docs/outline-traceability.md](docs/outline-traceability.md) | Đề cương → module → báo cáo → trạng thái |
| [docs/test-plan.md](docs/test-plan.md) | Ca kiểm thử UC01–UC07 |
| [docs/deployment.md](docs/deployment.md) | Chạy local, Colab, Hugging Face Spaces |
| [docs/roadmap.md](docs/roadmap.md) | Việc cần làm tiếp |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Quy ước nhánh, commit, chia việc |

## 9. Cấu hình (`.env`)

| Biến | Ý nghĩa |
|---|---|
| `DATABASE_URL` | Mặc định `sqlite:///./emovoice.db`; đổi sang PostgreSQL chỉ cần sửa biến này |
| `SECRET_KEY` | Chuỗi bí mật dài, ngẫu nhiên (bắt buộc đổi khi triển khai) |
| `MAX_UPLOAD_MB`, `ALLOWED_AUDIO` | Giới hạn dung lượng (mặc định 10 MB) và định dạng (`wav,mp3`) |
| `LOW_CONFIDENCE_THRESHOLD` | Ngưỡng cảnh báo độ tin cậy thấp (mặc định 0,30) |
| `MODEL_CHECKPOINT_PATH` | Đường dẫn checkpoint, mặc định `ml/weights/best_distilhubert_lora.pt` |
| `PASSWORD_RESET_TTL_MINUTES` | Thời hạn mã đặt lại mật khẩu |
| `DEV_BYPASS_LOGIN` | `1` hiện nút Vào thử (chỉ dùng khi phát triển) |
| `ENABLE_ADMIN_EXTRA_PAGES` | `1` bật 2 trang admin chưa có thiết kế |
| `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Tài khoản admin mặc định do `db/seed.py` tạo (đổi mật khẩu trước khi triển khai) |
| `SERVER_PORT` | Cổng chạy, mặc định 7860 |

Không commit file `.env`, file `*.db` và checkpoint `*.pt`.

## 10. Xử lý sự cố

| Triệu chứng | Cách xử lý |
|---|---|
| `ModuleNotFoundError: No module named 'gradio'` | Chưa kích hoạt đúng môi trường. Chạy lại `conda activate emovoice` hoặc kích hoạt `.venv`, kiểm tra bằng `python -c "import gradio"` |
| Icon hiện thành chữ (`mic`, `graphic_eq`) | Máy chưa tải được Google Fonts (offline hoặc bị chặn). Kết nối Internet rồi tải lại trang |
| Cổng 7860 đã bị dùng | Đổi `SERVER_PORT` trong `.env` |
| `conda` không được nhận trong PowerShell | Mở Anaconda Prompt, hoặc chạy `conda init powershell` rồi mở lại terminal |
| PowerShell chặn kích hoạt `.venv` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Lỗi `torchao` khi tạo LoRA | `pip install --upgrade "torchao>=0.16.0"` |
| Giao diện không đổi sau khi sửa CSS | CSS nạp khi khởi động; dừng `python app.py` rồi chạy lại và tải lại trang (Ctrl+F5) |
