# Triển khai

Ứng dụng là một tiến trình Gradio duy nhất (`python app.py`). Đề cương nêu môi trường: Google Colab (GPU miễn phí), Kaggle, VS Code; ứng dụng demo: Web (Gradio).

## 1. Chạy local (Windows / Linux / macOS)

```powershell
cd emovoice
python -m venv .venv
.\.venv\Scripts\Activate.ps1                 # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
Copy-Item .env.example .env                  # chỉnh SECRET_KEY, ADMIN_PASSWORD
# đặt best_distilhubert_lora.pt vào ml/weights/  (đã ignore khỏi git)
python app.py                                # mở http://127.0.0.1:7860 (SERVER_PORT trong .env)
```

Xem giao diện khi chưa có mô hình/CSDL: đặt `DEV_BYPASS_LOGIN=1` trong `.env` để có nút "Vào thử (Người dùng/Quản trị viên)"; thêm `ENABLE_ADMIN_EXTRA_PAGES=1` để hiện 2 trang admin chưa có Stitch. **Luôn để `DEV_BYPASS_LOGIN=0` khi triển khai.**

Gradio đọc `GRADIO_SERVER_NAME` (ví dụ `0.0.0.0` để máy khác trong mạng truy cập) và `GRADIO_SERVER_PORT`; `SERVER_PORT` của dự án ưu tiên hơn.

Font Be Vietnam Pro, Inter và icon Material Symbols nạp từ Google Fonts nên máy chạy cần Internet; offline icon sẽ hiện thành chữ (TODO: lưu font cục bộ).

## 2. Google Colab (liên kết chia sẻ)

```python
# Ô 1: cài đặt (runtime GPU T4)
!git clone <repo của nhóm> emovoice && cd emovoice && pip install -r requirements.txt
# Ô 2: nối Drive để lấy checkpoint rồi chép vào ml/weights/
from google.colab import drive; drive.mount('/content/drive')
!cp "/content/drive/MyDrive/<thư mục>/best_distilhubert_lora.pt" emovoice/ml/weights/
# Ô 3: chạy với liên kết công khai
%cd emovoice
import os; os.environ["DEV_BYPASS_LOGIN"] = "0"
from app import demo
demo.queue().launch(share=True)   # in ra URL dạng https://xxxx.gradio.live (hết hạn sau ~1 tuần)
```

Lưu ý: liên kết `share=True` công khai ra Internet — chỉ dùng cho buổi báo cáo/demo, đặt mật khẩu admin mạnh. SQLite trên Colab mất khi runtime bị thu hồi; seed lại mỗi phiên hoặc lưu `emovoice.db` lên Drive. Từ Gradio 6, `theme/css/head` truyền ở `launch()`: dùng `python app.py` (đã xử lý sẵn) hoặc gọi `demo.launch(share=True, **theme.app_kwargs()[1])`.

## 3. Hugging Face Spaces

1. Tạo Space, SDK **Gradio**, `app_file: app.py` (file `README.md` của Space cần phần metadata YAML; không trộn với README này nếu dùng chung repo).
2. `requirements.txt` ở gốc đã đủ; `torch` trên Spaces CPU nên dùng bản CPU để build nhanh (chỉ định index trong `requirements.txt` của Space).
3. Checkpoint 90,6 MiB: dùng Git LFS hoặc tải từ Hugging Face Hub khi khởi động; **không** đưa `.env` lên repo — đặt `SECRET_KEY`, `ADMIN_PASSWORD`, `DATABASE_URL` bằng *Secrets* của Space.
4. Hệ tệp của Space là tạm thời: SQLite và `storage/` mất khi Space khởi động lại. Với dữ liệu cần giữ, bật Persistent Storage (đặt `DATABASE_URL=sqlite:////data/emovoice.db`) hoặc dùng PostgreSQL ngoài (chỉ đổi `DATABASE_URL`).
5. `DEV_BYPASS_LOGIN=0`, `ENABLE_ADMIN_EXTRA_PAGES` theo nhu cầu.

## 4. GPU / CPU và thời gian suy luận

| Môi trường | Số liệu có trong báo cáo | Ghi chú |
|---|---|---|
| GPU (T4, Colab) | DistilHuBERT + LoRA **7,60 ms/mẫu** (có warm-up + `torch.cuda.synchronize`, batch 16, báo cáo Mục 5.1.3) | Số này chỉ là suy luận mô hình, chưa gồm tiền xử lý |
| CPU | **Chưa đo** | Cần đo bằng `ml/benchmark.py`; yêu cầu: tiền xử lý + suy luận < 1,5 s cho đoạn 3 s |

- Lần suy luận đầu chậm hơn do nạp mô hình/warm-up: nạp một lần khi khởi động (`inference_service.load_model_once`) và chạy 1–2 lần khởi động trước khi nhận yêu cầu.
- Space CPU miễn phí và Colab CPU có thể chậm; thu âm trực tiếp trên Colab/Spaces cần trình duyệt cấp quyền micro (HTTPS — `gradio.live` và `hf.space` đều có).
- Giới hạn tải lên `MAX_UPLOAD_MB=10`; đoạn khuyến nghị 1–5 giây (mô hình cố định 3 giây).
- LoRA có thể gộp vào trọng số gốc khi triển khai để không tăng độ trễ (báo cáo Mục 5.1.3); chưa thực hiện, chưa Pruning/lượng tử hóa.
