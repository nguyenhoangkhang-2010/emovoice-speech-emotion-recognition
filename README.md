# EmoVoice

Ứng dụng web nhận diện cảm xúc qua giọng nói (Speech Emotion Recognition, SER) xây bằng **Gradio**. Mô hình **DistilHuBERT + LoRA + Temporal Attention Pooling** phân loại 8 cảm xúc và giải thích quyết định bằng biểu đồ chú ý (XAI) theo thời gian.

Đề tài khóa luận CNTT-KLCN311 (Khoa CNTT, Trường ĐH Công Thương TP.HCM): *Cải tiến thuật toán nhận diện cảm xúc qua giọng nói (SER) bằng transformer*.

Ứng dụng đã chạy end-to-end: đăng ký và đăng nhập thật, thu âm hoặc tải tệp, tiền xử lý, suy luận bằng mô hình thật, XAI, lưu lịch sử vào cơ sở dữ liệu và các trang quản trị. Kết quả chỉ mang tính tham khảo (xem mục 11).

## 1. Tính năng

| Nhóm | Nội dung |
|---|---|
| Công khai | Đăng nhập, Đăng ký, Quên mật khẩu (mã 6 số gửi qua email), trang **Giới thiệu**, trang **Hướng dẫn** |
| Người dùng | **Phân tích cảm xúc** (tải WAV/MP3 hoặc thu âm trực tiếp), **Lịch sử phân tích** (của riêng tài khoản), **Tài khoản của tôi** |
| Quản trị viên | Toàn bộ chức năng của người dùng, cộng thêm: **Tổng quan**, **Mô hình & hiệu năng**, **Quản lý người dùng**, **Nhật ký hệ thống**; đặt `ENABLE_ADMIN_EXTRA_PAGES=1` để có thêm **Quản lý mô hình AI** và **Quản lý dữ liệu âm thanh** |

Trang **Phân tích cảm xúc**:

- Nhập âm thanh từ tệp (WAV hoặc MP3, tối đa 10 MB) hoặc thu trực tiếp qua micro. Tệp sai định dạng, rỗng, quá lớn hoặc hỏng bị chặn trước khi suy luận.
- Tiền xử lý tự động: 16 kHz mono, cắt khoảng lặng (`top_db = 25`), chuẩn hóa biên độ, cố định 3 giây (48.000 mẫu).
- Kết quả: nhãn cảm xúc, độ tin cậy, phân phối Softmax của 8 nhãn, cảnh báo khi mọi xác suất dưới 30%.
- XAI: bản đồ chú ý 5 mức trên dạng sóng, Mel-spectrogram có lớp phủ vùng chú ý, tải ảnh kết quả.
- Tùy chọn so sánh với baseline Random Forest (không có XAI, không lưu lịch sử).
- Tài khoản thật được lưu lịch sử: tệp âm thanh, kết quả, ảnh XAI; lịch sử có lọc, phân trang, nghe lại, xuất CSV và JSON.

Trang quản trị: thống kê và trạng thái dịch vụ, chỉ số mô hình đọc từ cơ sở dữ liệu (kèm ma trận nhầm lẫn), khóa hoặc mở khóa tài khoản, đổi vai trò, cấp mật khẩu tạm, thêm tài khoản (popup), nhật ký hoạt động có lọc, chọn mô hình đang dùng, nghe và xóa mẫu âm thanh.

8 nhãn cảm xúc: neutral (Trung tính), calm (Êm đềm), happy (Vui vẻ), sad (Buồn bã), angry (Tức giận), fearful (Sợ hãi), disgust (Chán ghét), surprised (Ngạc nhiên).

## 2. Kiến trúc

Một tiến trình Gradio duy nhất, bốn tầng phụ thuộc một chiều từ trên xuống:

```text
Trình duyệt ──▶ ui/ (Gradio Blocks, sự kiện) ──▶ services/ (nghiệp vụ, kiểm tra quyền)
                                                     ├──▶ ml/       tiền xử lý, DistilHuBERT + LoRA, XAI, baseline
                                                     ├──▶ models/   bảng SQLAlchemy (PostgreSQL, Alembic)
                                                     └──▶ storage/  tệp tải lên, ảnh heatmap và Mel
```

- Phiên đăng nhập (`SessionUser`) nằm trong `gr.State` phía máy chủ, theo từng tab trình duyệt. Mật khẩu băm bằng bcrypt.
- Phân quyền ba lớp: ẩn nhóm quản trị ở sidebar, `show_page` chặn trang, và mọi handler admin gọi `guard_admin` kiểm tra lại vai trò trong cơ sở dữ liệu. Ẩn menu chỉ là UX.
- Mô hình được nạp một lần ở lần phân tích đầu tiên rồi giữ trong bộ nhớ. Chỉ số mô hình (Accuracy, Macro F1, dung lượng, độ trễ) không viết cứng vào giao diện mà do lệnh đăng ký mô hình đo thật và ghi vào bảng `models`.
- Chi tiết: [docs/architecture.md](docs/architecture.md).

## 3. Yêu cầu

- Python **3.10 – 3.12** (đã chạy với Python 3.11, Gradio 6.30, PyTorch 2.14, Transformers 5.19, PEFT 0.21, SQLAlchemy 2.1).
- **PostgreSQL 17** cho môi trường chính thức (SQLite đủ để chạy thử và kiểm thử).
- Internet khi mở giao diện để tải font và icon từ Google Fonts; offline thì icon hiện thành chữ (ví dụ `mic`).
- GPU NVIDIA là tùy chọn. CPU vẫn chạy được: một lần phân tích 3 giây (tiền xử lý, suy luận, vẽ 2 ảnh XAI) mất khoảng 1,3 giây trên CPU i7-12700H; lần đầu sau khi khởi động mất thêm khoảng 16 giây để nạp mô hình.
- Trình duyệt chỉ cho dùng micro khi trang chạy ở `localhost` hoặc HTTPS.

## 4. Cài đặt

```bash
git clone https://github.com/nguyenhoangkhang-2010/emovoice-speech-emotion-recognition.git
cd emovoice-speech-emotion-recognition
```

Tạo môi trường (chọn một):

```bash
# Anaconda
conda create -n emovoice python=3.11 -y
conda activate emovoice
```

```powershell
# venv trên Windows (PowerShell). Nếu bị chặn script: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```bash
# venv trên macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

Cài thư viện:

```bash
pip install -r requirements.txt
pip install --upgrade "torchao>=0.16.0"
```

Nếu có card NVIDIA, cài bản PyTorch CUDA theo hướng dẫn ở trang chủ PyTorch **trước** khi chạy `pip install -r requirements.txt` để khỏi phải gỡ cài lại. `peft` cần `torchao>=0.16`.

Tạo tệp cấu hình rồi chỉnh các giá trị (xem mục 8):

```bash
cp .env.example .env          # PowerShell: Copy-Item .env.example .env
```

## 5. Khởi tạo cơ sở dữ liệu và mô hình

**PostgreSQL** (môi trường chính thức): tạo cơ sở dữ liệu rỗng `emovoice`, đặt `DATABASE_URL=postgresql+psycopg2://<user>:<mat_khau>@localhost:5432/emovoice` trong `.env`, rồi:

```bash
alembic upgrade head          # tạo 9 bảng
python -m db.seed             # 8 nhãn cảm xúc và tài khoản admin từ ADMIN_* trong .env
```

**SQLite** (chạy thử nhanh): giữ `DATABASE_URL` mặc định, rồi:

```bash
python -c "from db.init_db import init_db; init_db()"
python -m db.seed
```

**Mô hình.** Đặt hai tệp trọng số vào `ml/weights/` (thư mục này không nằm trong git: `*.pt`, `*.pkl`, `*.npz` đều bị bỏ qua):

| Tệp | Vai trò |
|---|---|
| `final_distilhubert_lora_full.pt` | Mô hình chính, `state_dict` dùng cho suy luận và XAI |
| `final_rf_baseline.pkl` | Random Forest (212 đặc trưng) chỉ để đối chiếu |

Đặt tập kiểm thử `waveforms_cache.npz` (và `features_212_cache.npz` cho baseline) ở đường dẫn `EVAL_DATASET_PATH` / `EVAL_FEATURES_PATH`, rồi đăng ký để đo thật và ghi vào bảng `models`:

```bash
# mô hình chính: nạp, đánh giá trên 180 mẫu Test, đo độ trễ, ghi DB và đặt làm mô hình đang dùng
python -m ml.register_model --checkpoint ml/weights/final_distilhubert_lora_full.pt --activate
# baseline Random Forest (để so sánh, không dùng suy luận chính vì không có attention)
python -m ml.register_baseline --checkpoint ml/weights/final_rf_baseline.pkl
```

Với checkpoint bàn giao, lệnh đo được Accuracy 75,00% và Macro F1 73,13% trên tập Test độc lập 180 mẫu (RAVDESS, diễn viên 22–24); 249.353 trên 23.741.321 tham số được huấn luyện (1,05%), dung lượng 90,6 MiB. Độ trễ do máy chạy lệnh đo và ghi kèm thiết bị (CPU chậm hơn nhiều so với GPU).

## 6. Chạy ứng dụng

```bash
python app.py
```

Mở <http://127.0.0.1:7860> (đổi cổng bằng `SERVER_PORT`). Đăng nhập bằng tài khoản admin do `db.seed` tạo (`ADMIN_USERNAME` / `ADMIN_PASSWORD` trong `.env`), hoặc đăng ký tài khoản mới.

Khi phát triển có thể đặt `DEV_BYPASS_LOGIN=1` để hiện hai nút **Vào thử (Người dùng)** và **Vào thử (Quản trị viên)**: dùng được mọi chức năng phân tích nhưng không lưu lịch sử. Khi triển khai thật phải để `DEV_BYPASS_LOGIN=0` (máy chủ từ chối cả khi bị gọi trực tiếp).

Quên mật khẩu gửi mã 6 số qua email nên cần cấu hình `SMTP_*`. Chưa có SMTP thì đặt `RESET_CODE_ON_SCREEN=1` để hiện mã ngay trên giao diện; chế độ này chỉ dành cho demo vì ai biết email cũng nhận được mã.

## 7. Kiểm thử

```bash
pytest
```

222 ca kiểm thử cho tài khoản, quên mật khẩu, tiền xử lý, suy luận, XAI, lịch sử, phân quyền, quản trị, nhật ký, đăng ký mô hình và baseline. Bộ kiểm thử dùng cơ sở dữ liệu SQLite tạm, không đụng tới cơ sở dữ liệu thật, và mất khoảng 1 phút. Kế hoạch kiểm thử thủ công theo Use-Case: [docs/test-plan.md](docs/test-plan.md).

## 8. Cấu hình (`.env`)

Mẫu đầy đủ ở [`.env.example`](.env.example).

| Biến | Ý nghĩa |
|---|---|
| `DATABASE_URL` | Mặc định `sqlite:///./emovoice.db`; đổi sang PostgreSQL chỉ cần sửa biến này |
| `SECRET_KEY` | Chuỗi bí mật dài, ngẫu nhiên (bắt buộc đổi khi triển khai) |
| `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Tài khoản admin mặc định do `db/seed.py` tạo; đổi mật khẩu trước khi triển khai |
| `MAX_UPLOAD_MB`, `ALLOWED_AUDIO` | Dung lượng tối đa (mặc định 10 MB) và định dạng (`wav,mp3`) |
| `LOW_CONFIDENCE_THRESHOLD` | Ngưỡng cảnh báo độ tin cậy thấp (mặc định 0,30) |
| `MODEL_CHECKPOINT_PATH` | Checkpoint dự phòng khi bảng `models` chưa có mô hình đang dùng |
| `EVAL_DATASET_PATH`, `EVAL_FEATURES_PATH` | Tập kiểm thử cho mô hình chính và baseline; chỉ dùng khi đăng ký mô hình |
| `PASSWORD_RESET_TTL_MINUTES` | Thời hạn mã đặt lại mật khẩu (mặc định 15 phút) |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | Gửi email mã đặt lại (cổng 587 STARTTLS hoặc 465 SSL); để trống `SMTP_HOST` thì chưa gửi được |
| `RESET_CODE_ON_SCREEN` | `1` hiện mã ngay trên giao diện; chỉ để demo, không an toàn |
| `DEV_BYPASS_LOGIN` | `1` hiện nút Vào thử; chỉ khi phát triển |
| `ENABLE_ADMIN_EXTRA_PAGES` | `1` hiện thêm 2 trang admin: Quản lý mô hình AI, Quản lý dữ liệu âm thanh |
| `SERVER_PORT` | Cổng chạy, mặc định 7860 |

Không commit `.env`, `*.db`, `*.pt`, `*.pkl`, `*.npz` và nội dung `storage/`, `logs/` (đã có trong `.gitignore`).

## 9. Mô hình

`ntu-spml/distilhubert` (đóng băng) + LoRA (r=8, alpha=16, dropout=0,1, gắn vào `q_proj` và `v_proj`) + Temporal Attention Pooling (Linear 768→1, softmax theo thời gian, 149 khung cho 3 giây) + đầu phân loại 768→256→GELU→LayerNorm→Dropout(0,3)→8. Hàm `forward` trả về `(logits, attn_weights)`; `attn_weights` là nguồn của mọi biểu đồ XAI.

Mức chú ý trên biểu đồ được gom từ 149 khung thành 30 ô (mỗi ô 0,1 giây) rồi chia 5 mức theo tỷ lệ so với ô lớn nhất của chính mẫu đó. Vì vậy màu chỉ so sánh được trong cùng một mẫu, và attention chỉ là công cụ hỗ trợ diễn giải, không phải lời giải thích đầy đủ.

## 10. Cấu trúc thư mục

```text
emovoice/
  app.py                 điểm vào duy nhất (Gradio)
  core/                  config (.env), security (bcrypt), session (SessionUser, require_login, require_admin), logging
  db/                    base, session, init_db, seed
  models/                9 bảng SQLAlchemy: users, audio_files, audio_features, emotions, predictions,
                         prediction_scores, models, system_logs, password_resets
  migrations/            Alembic (alembic.ini ở gốc)
  services/              auth, account, audio, preprocessing, inference, xai, baseline, history,
                         admin, model, system_status, audit, mail
  ml/                    config, preprocess, model, inference, xai, baseline, datasets, evaluate, benchmark,
                         register_model, register_baseline, weights/
  ui/                    layout, render, theme, i18n_vi, css/, templates/, components/, pages/
  stitch/                bản sao nguyên bản thiết kế Stitch (images/, html/, DESIGN.md)
  storage/               uploads/, heatmaps/, mel/ (tệp tải lên và ảnh XAI, không nằm trong git)
  logs/                  nhật ký kỹ thuật ra tệp emovoice.log (xoay vòng 2 MB × 5 bản); nhật ký nghiệp vụ cho admin nằm ở bảng system_logs
  tests/                 pytest
  docs/                  tài liệu thiết kế
```

Quy ước: chuỗi hiển thị tiếng Việt chỉ đặt trong `ui/i18n_vi.py`; màu và bo góc chỉ dùng token trong `ui/css/tokens.css` (giao diện phẳng, không gradient); mọi handler admin phải gọi `guard_admin` ở dòng đầu.

## 11. Giới hạn đã biết

- Mô hình huấn luyện trên RAVDESS (giọng diễn xuất tiếng Anh, 24 diễn viên). Với giọng tự nhiên hoặc tiếng Việt, kết quả có thể kém hơn; chưa kiểm thử chéo trên TESS hoặc CREMA-D.
- Ứng dụng xử lý từng đoạn âm thanh hoàn chỉnh dài tối đa 3 giây, chưa phân tích luồng âm thanh liên tục.
- Chạy một tiến trình với một bản mô hình: phù hợp trình diễn và nhóm dùng nhỏ, chưa phải kiến trúc cho tải lớn.
- Khóa hoặc hạ quyền một tài khoản không ngắt phiên đang mở; chỉ các chức năng admin kiểm tra lại vai trò trong cơ sở dữ liệu ở mỗi lần gọi.
- Tài khoản được cấp mật khẩu tạm chưa bị buộc đổi mật khẩu ở lần đăng nhập đầu.
- Kết quả của baseline Random Forest không được lưu vào lịch sử; 1D-CNN, XGBoost và Bi-LSTM chưa được tích hợp vào ứng dụng.
- Chưa có Pruning hay lượng tử hóa; chưa đo trực tiếp HuBERT gốc để so sánh kích thước và độ trễ.

## 12. Tài liệu

| Tệp | Nội dung |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Kiến trúc Gradio, DFD mức 0 và 1, luồng phân tích |
| [docs/use-cases.md](docs/use-cases.md) | Use-Case UC01–UC07 |
| [docs/database.md](docs/database.md) | 9 bảng, quan hệ |
| [docs/class-diagram.md](docs/class-diagram.md) | Sơ đồ lớp (Mermaid) |
| [docs/ui-pages.md](docs/ui-pages.md) | Các trang, phân quyền |
| [docs/stitch-mapping.md](docs/stitch-mapping.md) | Stitch → module → component, token màu |
| [docs/outline-traceability.md](docs/outline-traceability.md) | Đề cương → module → báo cáo → trạng thái |
| [docs/test-plan.md](docs/test-plan.md) | Ca kiểm thử UC01–UC07 |
| [docs/deployment.md](docs/deployment.md) | Chạy local, Colab, Hugging Face Spaces |
| [docs/roadmap.md](docs/roadmap.md) | Lộ trình theo đề cương |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Quy ước nhánh, commit, chia việc |

Một số tệp trong `docs/` được viết từ giai đoạn skeleton nên còn ghi trạng thái cũ ở vài chỗ.

## 13. Xử lý sự cố

Khi gặp lỗi, xem lần lượt: (1) thông báo hiện trên giao diện, mỗi thông báo lỗi đầu vào có mã như `UC02-E1`; (2) cửa sổ terminal đang chạy `python app.py`; (3) trang **Nhật ký hệ thống** của quản trị viên, nơi ghi các lỗi tải tệp, tiền xử lý và suy luận (ví dụ mức `ERROR`, dịch vụ `inference`); (4) tệp `logs/emovoice.log`, nơi có đầy đủ traceback của lỗi (trang Nhật ký hệ thống chỉ giữ một dòng tóm tắt) và vẫn đọc được khi cơ sở dữ liệu không kết nối được.

### Cài đặt và khởi động

| Triệu chứng | Nguyên nhân thường gặp và cách xử lý |
|---|---|
| `ModuleNotFoundError: No module named 'gradio'` (hoặc `torch`, `peft`...) | Chưa kích hoạt đúng môi trường hoặc chưa cài `requirements.txt`. Kiểm tra bằng `python -c "import gradio"` |
| Lỗi `torchao` khi tạo LoRA | `pip install --upgrade "torchao>=0.16.0"` |
| `OSError: Cannot find empty port` | Cổng 7860 đang bị chương trình khác dùng. Đổi `SERVER_PORT` trong `.env` hoặc tắt tiến trình cũ |
| Lần phân tích đầu tiên chạy rất lâu, hoặc báo lỗi tải về từ Hugging Face | Mô hình gốc `ntu-spml/distilhubert` (khoảng 94 MB) được tải từ Hugging Face ở lần nạp đầu tiên, nên cần Internet. Sau khi đã tải, có thể chạy offline bằng biến môi trường `HF_HUB_OFFLINE=1` |
| Icon hiện thành chữ (`mic`, `graphic_eq`) | Máy chưa tải được Google Fonts. Kết nối Internet rồi tải lại trang |
| Sửa CSS nhưng giao diện không đổi | CSS chỉ được nạp khi khởi động. Dừng `python app.py`, chạy lại rồi tải lại trang (Ctrl+F5) |
| PowerShell chặn kích hoạt `.venv` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |

### Cơ sở dữ liệu

| Triệu chứng | Nguyên nhân thường gặp và cách xử lý |
|---|---|
| Giao diện báo "Không kết nối được cơ sở dữ liệu. Vui lòng thử lại sau." hoặc `alembic upgrade head` không kết nối được | Kiểm tra dịch vụ PostgreSQL đang chạy, cơ sở dữ liệu `emovoice` đã tạo, và `DATABASE_URL` đúng dạng `postgresql+psycopg2://user:mat_khau@localhost:5432/emovoice` |
| `no such table: ...` (SQLite) hoặc `relation ... does not exist` (PostgreSQL) | Chưa tạo bảng. Chạy `alembic upgrade head` (PostgreSQL) hoặc `init_db()` (SQLite), rồi `python -m db.seed` |
| Trang quản trị báo "Không truy cập được bảng models" | Cùng nguyên nhân hai dòng trên: sai `DATABASE_URL` hoặc chưa chạy `alembic upgrade head` |
| Không đăng nhập được bằng tài khoản admin | `db.seed` chưa chạy. Nếu đã chạy trước khi đổi `ADMIN_PASSWORD` trong `.env`, mật khẩu mới không được áp dụng, vì `db.seed` chỉ tạo admin khi chưa có. Hãy đổi mật khẩu ở trang Tài khoản của tôi hoặc nhờ quản trị viên khác cấp mật khẩu tạm |

### Mô hình

| Triệu chứng | Nguyên nhân thường gặp và cách xử lý |
|---|---|
| Thông báo "Mô hình chưa sẵn sàng": *Chưa có mô hình đang dùng...* | Bảng `models` chưa có mô hình đang dùng và không thấy tệp `.pt` ở `MODEL_CHECKPOINT_PATH`. Đặt tệp vào `ml/weights/` rồi chạy `python -m ml.register_model --checkpoint <tệp .pt> --activate` (xem mục 5) |
| Thông báo "Mô hình chưa sẵn sàng": *Không thấy tệp checkpoint của mô hình đang dùng...* | Bảng `models` còn lưu đường dẫn cũ (ví dụ sau khi chuyển máy hoặc đổi thư mục). Chạy lại `register_model ... --activate` với đường dẫn mới |
| `Missing key(s)` hoặc `size mismatch` khi nạp checkpoint | Tệp `.pt` không đúng kiến trúc (LoRA r=8 gắn `q_proj`/`v_proj`, đầu phân loại 768→256→8). Dùng đúng tệp `final_distilhubert_lora_full.pt` hoặc `best_distilhubert_lora.pt` của đề tài |
| `register_model` báo không thấy tập kiểm thử | Đặt `waveforms_cache.npz` (có `X_test`, `y_test`) đúng `EVAL_DATASET_PATH`. Với baseline cần `features_212_cache.npz` ở `EVAL_FEATURES_PATH` |
| `register_baseline` báo số đặc trưng không phải 212 | Tệp `.pkl` không phải Random Forest 212 đặc trưng của đề tài |
| Trang Mô hình & hiệu năng hoặc Quản lý mô hình AI trống | Chưa đăng ký mô hình nào. Chạy `register_model` (và `register_baseline` nếu muốn so sánh) |

### Phân tích âm thanh

| Triệu chứng | Nguyên nhân thường gặp và cách xử lý |
|---|---|
| "Lỗi định dạng âm thanh" (`UC02-E1`) | Tệp không phải WAV hoặc MP3, vượt 10 MB (`MAX_UPLOAD_MB`), rỗng hoặc bị hỏng. Thông báo ghi rõ lý do |
| "Không đọc được âm thanh" (`UC02-E2`) | Tệp có đuôi đúng nhưng không giải mã được. Chuyển sang WAV rồi thử lại, hoặc cài `ffmpeg` để librosa đọc được các MP3 khó |
| "Chưa có âm thanh" (`UC02-W1`) | Bấm phân tích khi chưa chọn tệp hoặc chưa thu âm. Chọn tab đang dùng rồi cung cấp âm thanh |
| Không thu âm được | Cấp quyền micro cho trình duyệt. Trang chỉ được dùng micro khi chạy ở `localhost` hoặc HTTPS. Kiểm tra thiết bị ghi mặc định của hệ điều hành |
| Banner "Độ tin cậy thấp" | Mọi xác suất đều dưới 30% (`LOW_CONFIDENCE_THRESHOLD`). Thu lại ở nơi yên tĩnh, một người nói, 1–5 giây. Kết quả vẫn được hiển thị nhưng không đáng tin |
| Có kết quả nhưng không thấy trong Lịch sử | Đang dùng tài khoản Vào thử ("Phiên thử nghiệm" không lưu lịch sử), hoặc gặp lỗi ghi dữ liệu ("Chưa lưu được lịch sử"): kiểm tra kết nối cơ sở dữ liệu |
| Không có ảnh XAI nhưng vẫn có nhãn cảm xúc | Vẽ ảnh bằng matplotlib bị lỗi; kết quả phân loại vẫn đúng. Xem terminal và Nhật ký hệ thống |
| Phân tích chậm | Lần đầu sau khi khởi động mất khoảng 16 giây để nạp mô hình (CPU). Các lần sau khoảng 1,3 giây trên CPU. Có GPU NVIDIA thì cài PyTorch bản CUDA để nhanh hơn |

### Tài khoản và quyền

| Triệu chứng | Nguyên nhân thường gặp và cách xử lý |
|---|---|
| "Đăng nhập sai quá nhiều lần. Vui lòng thử lại sau vài phút." | Sai 5 lần trong 10 phút thì tạm khóa đăng nhập. Chờ rồi thử lại |
| "Tài khoản đã bị khóa" | Quản trị viên đã khóa tài khoản. Nhờ quản trị viên mở khóa ở trang Quản lý người dùng |
| Không nhận được mã đặt lại mật khẩu | Chưa cấu hình `SMTP_*` (giao diện báo "Chức năng gửi email chưa được cấu hình"), hoặc thư vào hộp thư rác. Với Gmail dùng cổng 587 và mật khẩu ứng dụng (App password). Khi demo có thể đặt `RESET_CODE_ON_SCREEN=1` |
| "Mã không hợp lệ hoặc đã hết hạn" | Thông báo chung cho email chưa đăng ký, mã sai, mã quá 15 phút hoặc đã dùng. Sai quá 5 lần thì mã bị hủy; phải xin mã mới, và chỉ xin lại được sau 60 giây |
| Không thấy nút Vào thử | Đặt `DEV_BYPASS_LOGIN=1` trong `.env` rồi khởi động lại |
| Không thấy trang Quản lý mô hình AI hoặc Quản lý dữ liệu âm thanh | Đặt `ENABLE_ADMIN_EXTRA_PAGES=1` trong `.env` rồi khởi động lại, và đăng nhập bằng tài khoản quản trị |
| "Bạn không có quyền thực hiện thao tác này" | Tài khoản không phải quản trị viên, hoặc vai trò vừa bị đổi. Đăng nhập lại bằng tài khoản có quyền |
