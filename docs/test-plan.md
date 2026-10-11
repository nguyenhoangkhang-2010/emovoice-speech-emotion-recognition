# Kế hoạch kiểm thử (đề cương: "Kiểm thử và triển khai hệ thống", CLO4)

Trạng thái: **Chưa làm** (chưa có mã để chạy), **Skip** (có test khung `pytest.skip` trong `tests/` kèm TODO), **Đạt** (đã chạy). Cột "File test" là nơi sẽ viết test tự động; nhiều ca cần kiểm tra thủ công trên giao diện.

Hiện chỉ có 1 test thật: `TC-UC06-05` (`core.session.require_admin`) — đã chạy thử với một bản pytest giả tối thiểu và đạt; pytest thật chưa được cài trong môi trường hiện tại nên chưa chạy qua `python -m pytest tests` (11 test còn lại là skip có TODO).

## UC01 — Đăng ký, đăng nhập, đăng xuất, quên mật khẩu

| ID | UC | Mô tả | Dữ liệu vào | Kết quả mong đợi | File test | Trạng thái |
|---|---|---|---|---|---|---|
| TC-UC01-01 | UC01 | Đăng ký hợp lệ | username `an01`, email `an01@x.vn`, mật khẩu 8+ ký tự | Tạo `users` role `User`; cột `password` là hash bcrypt, không chứa mật khẩu thô | `test_auth.py` | Skip |
| TC-UC01-02 | UC01 | Đăng ký trùng username/email | username hoặc email đã tồn tại | Thông báo "đã được sử dụng", không tạo bản ghi | `test_auth.py` | Skip |
| TC-UC01-03 | UC01 | Mật khẩu nhập lại không khớp | `password` ≠ `confirm` | Thông báo "Mật khẩu nhập lại không khớp." | thủ công | Chưa làm |
| TC-UC01-04 | UC01 | Đăng nhập đúng | tài khoản + mật khẩu đúng | `SessionUser` vào `gr.State`; chuyển sang trang Phân tích; form bị xóa mật khẩu | `test_auth.py` | Skip |
| TC-UC01-05 | UC01 | Đăng nhập sai mật khẩu | mật khẩu sai | "Sai tài khoản hoặc mật khẩu"; không có phiên | `test_auth.py` | Skip |
| TC-UC01-06 | UC01 | Tài khoản bị khóa | `is_active = false` | Từ chối đăng nhập | `test_auth.py` | Skip |
| TC-UC01-07 | UC01 | Đăng xuất | bấm "Đăng xuất" | `gr.State` về `None`, quay về view đăng nhập, nhóm Quản trị ẩn | thủ công | Chưa làm |
| TC-UC01-08 | UC01 | Yêu cầu mã đặt lại | email tồn tại / không tồn tại | Cùng một thông báo cho cả hai trường hợp; chỉ lưu `token_hash`, `expires_at` = +15 phút | `test_password_reset.py` | Skip |
| TC-UC01-09 | UC01 | Đặt lại mật khẩu | mã đúng + mật khẩu mới | Mật khẩu đổi, `used_at` được đặt; mã dùng lại bị từ chối | `test_password_reset.py` | Skip |
| TC-UC01-10 | UC01 | Mã hết hạn | mã quá 15 phút | Từ chối, yêu cầu gửi mã mới | `test_password_reset.py` | Skip |
| TC-UC01-11 | UC01 | Nút "Vào thử" khi `DEV_BYPASS_LOGIN=0` | — | Không có nút; gọi handler trực tiếp bị từ chối | thủ công | Chưa làm |

## UC02 — Tải tệp hoặc thu âm

| ID | UC | Mô tả | Dữ liệu vào | Kết quả mong đợi | File test | Trạng thái |
|---|---|---|---|---|---|---|
| TC-UC02-01 | UC02 | Tải WAV hợp lệ | `.wav` ≤ 10 MB | Tệp được chấp nhận, hiện thời lượng | thủ công | Chưa làm |
| TC-UC02-02 | UC02 | Tải MP3 hợp lệ | `.mp3` ≤ 10 MB | Chấp nhận | thủ công | Chưa làm |
| TC-UC02-03 | UC02 | Sai định dạng | `.ogg`, `.txt` | Toast `UC02-E1`: "Định dạng không được hỗ trợ, vui lòng chọn WAV hoặc MP3." | thủ công | Chưa làm |
| TC-UC02-04 | UC02 | Quá dung lượng | tệp > `MAX_UPLOAD_MB` | Thông báo lỗi dung lượng | thủ công | Chưa làm |
| TC-UC02-05 | UC02 | Tệp hỏng (đuôi đúng, nội dung sai) | `.wav` rỗng/hỏng | Báo lỗi dữ liệu âm thanh bị hỏng, hủy tiến trình | thủ công | Chưa làm |
| TC-UC02-06 | UC02 | Bấm phân tích khi chưa có âm thanh | — | Toast cảnh báo "Chưa có âm thanh" | thủ công | Chưa làm |
| TC-UC02-07 | UC02 | Thu âm trực tiếp | micro hoạt động, 3 s | Tệp thu được xử lý như tệp tải lên | thủ công | Chưa làm |
| TC-UC02-08 | UC02 | Không có micro / chưa cấp quyền | từ chối quyền | Thông báo `UC03-W1` (khung Stitch ghi mã UC03-W1) | thủ công | Chưa làm |

## UC03 / UC07 — Tiền xử lý tự động

| ID | UC | Mô tả | Dữ liệu vào | Kết quả mong đợi | File test | Trạng thái |
|---|---|---|---|---|---|---|
| TC-UC03-01 | UC03/07 | Độ dài đầu ra cố định | tệp 1 s, 3 s, 6 s | Luôn `48.000` mẫu (pad số 0 hoặc cắt) | `test_preprocess.py` | Skip |
| TC-UC03-02 | UC03/07 | Tần số lấy mẫu và kênh | tệp 44,1 kHz stereo | Mono 16 kHz | `test_preprocess.py` | Skip |
| TC-UC03-03 | UC03/07 | Cắt khoảng lặng `top_db=25` | tệp có lặng hai đầu | Thời lượng sau cắt < thời lượng gốc, ghi `trimmed_duration` | `test_preprocess.py` | Skip |
| TC-UC03-04 | UC03/07 | Chuẩn hóa biên độ | tệp biên độ lớn/nhỏ | Giá trị trong `[-1, 1]` | `test_preprocess.py` | Skip |
| TC-UC03-05 | UC03/07 | Tệp toàn khoảng lặng | tệp im lặng | Không crash; cảnh báo `VAD-Null` ("Không phát hiện giọng nói rõ ràng") | `test_preprocess.py` | Skip |

## UC04 — Phân tích cảm xúc và XAI

| ID | UC | Mô tả | Dữ liệu vào | Kết quả mong đợi | File test | Trạng thái |
|---|---|---|---|---|---|---|
| TC-UC04-01 | UC04 | Hình dạng đầu ra | waveform 48.000 mẫu | `probs` 8 phần tử tổng = 1; `attn_weights` 149 khung | `test_inference.py` | Skip |
| TC-UC04-02 | UC04 | Hiển thị kết quả | tệp Angry rõ | Hero nhãn + độ tin cậy; 8 thanh xác suất; heatmap 5 mức; vạch kết thúc giọng nói | thủ công | Chưa làm |
| TC-UC04-03 | UC04 | Độ tin cậy thấp | mọi xác suất < 0,30 | Banner "Độ tin cậy thấp" | `test_inference.py` | Skip |
| TC-UC04-04 | UC04 | Thời gian xử lý | tệp 3 s, GPU và CPU | Tiền xử lý + suy luận < 1,5 s | `ml/benchmark.py` | Chưa làm |
| TC-UC04-05 | UC04 | Lưu lịch sử | phân tích thành công | 1 dòng `predictions` + 8 dòng `prediction_scores` | `test_inference.py` | Chưa làm |
| TC-UC04-06 | UC04 | XAI trên Mel-spectrogram | tệp bất kỳ | Ảnh attention phủ Mel (`render_attention_on_mel`) | thủ công | Chưa làm |

## UC05 — Lịch sử và danh sách mẫu

| ID | UC | Mô tả | Dữ liệu vào | Kết quả mong đợi | File test | Trạng thái |
|---|---|---|---|---|---|---|
| TC-UC05-01 | UC05 | Chỉ thấy bản ghi của mình | 2 user có dữ liệu | Mỗi user chỉ thấy lịch sử của mình | `test_history_filter.py` | Skip |
| TC-UC05-02 | UC05 | Lọc theo cảm xúc | chọn "Tức giận" | Chỉ còn bản ghi Angry | `test_history_filter.py` | Skip |
| TC-UC05-03 | UC05 | Lọc theo thời gian | "7 ngày qua" | Chỉ bản ghi trong 7 ngày | `test_history_filter.py` | Skip |
| TC-UC05-04 | UC05 | Tìm theo tên tệp | `khachhang` | Chỉ bản ghi khớp | `test_history_filter.py` | Skip |
| TC-UC05-05 | UC05 | Phân trang | 48 bản ghi, 10/trang | 5 trang; "Hiển thị 1–10 trong 48 kết quả"; Trước/Sau đúng | `test_history_filter.py` | Skip |
| TC-UC05-06 | UC05 | Drawer chi tiết | chọn một dòng | Drawer hiện waveform, heatmap, xác suất | thủ công | Chưa làm |
| TC-UC05-07 | UC05 | Trạng thái rỗng | bộ lọc không có kết quả | Hiện empty state + nút "Bắt đầu phân tích ngay" | thủ công | Chưa làm |

## UC06 — Quản trị

| ID | UC | Mô tả | Dữ liệu vào | Kết quả mong đợi | File test | Trạng thái |
|---|---|---|---|---|---|---|
| TC-UC06-01 | UC06 | Người thường không thấy nhóm Quản trị | đăng nhập `User` | Sidebar không có nhóm "QUẢN TRỊ HỆ THỐNG" | thủ công | Chưa làm |
| TC-UC06-02 | UC06 | Người thường vào trang admin | gọi `show_page("admin_users", user)` | Bị đưa về trang Phân tích | thủ công | Chưa làm |
| TC-UC06-03 | UC06 | Handler admin từ chối người thường | gọi `load_fn` / handler admin với `User` | `gr.Error`, không trả dữ liệu | `test_admin_access.py` | Skip |
| TC-UC06-04 | UC06 | Admin thấy đủ trang | đăng nhập `Admin` | Có Tổng quan, Người dùng, Nhật ký (+ 2 trang tùy chọn khi bật cờ) | thủ công | Chưa làm |
| TC-UC06-05 | UC06 | `require_admin` | `SessionUser` role `User` và `None` | Ném `PermissionDenied`; role `Admin` đi qua | `test_admin_access.py` | **Đạt** (pytest giả) |
| TC-UC06-06 | UC06 | Khóa/mở tài khoản | chọn người dùng, bấm nút | Trạng thái đổi, ghi `system_logs`; Admin không tự khóa mình | `test_admin_access.py` | Chưa làm |
| TC-UC06-07 | UC06 | Lọc nhật ký | mức `ERROR` | Chỉ dòng ERROR | thủ công | Chưa làm |
| TC-UC06-08 | UC06 | Số liệu mô hình đọc từ file | sửa `model_metrics.json` | Trang Mô hình & hiệu năng và Tổng quan đổi theo, không có số cứng trong code UI | thủ công | Chưa làm |

## Kiểm thử phi chức năng và đánh giá mô hình

| ID | Mô tả | Kết quả mong đợi | Trạng thái |
|---|---|---|---|
| TC-NF-01 | Mật khẩu băm | Không có mật khẩu thô trong DB và log | Chưa làm |
| TC-NF-02 | Giao diện sáng, không màu đen/gradient | Không có `?__theme=dark`, quét CSS không thấy `#000`/`gradient` | Một phần (đã quét CSS/HTML; chưa kiểm tra bằng mắt vì chưa chạy gradio) |
| TC-NF-03 | Kiểm thử chéo TESS và CREMA-D | Accuracy/F1 ghi vào `model_metrics.json` | Chưa làm |
| TC-NF-04 | So sánh trước/sau cải tiến (HuBERT-base, wav2vec 2.0 gốc so với DistilHuBERT + LoRA) cùng quy trình đo | Số tham số, MiB, ms/mẫu cho mọi mô hình | Chưa làm |
