# Các trang giao diện (Gradio)

Thiết kế làm bằng Stitch; file gốc sao chép nguyên bản vào `stitch/images` và `stitch/html`. Token màu/CSS nằm ở `ui/css/tokens.css` (không dùng màu đen, không gradient); chuỗi tiếng Việt ở `ui/i18n_vi.py`. Bảng đối chiếu chi tiết từng file Stitch → module → component → template: xem [stitch-mapping.md](stitch-mapping.md).

**WEB USER** = Đăng nhập/Đăng ký/Quên mật khẩu, Phân tích mới, Lịch sử phân tích, Mô hình & hiệu năng.
**WEB ADMIN** = toàn bộ trang user + nhóm "Quản trị hệ thống": Tổng quan, Quản lý người dùng, Nhật ký hệ thống (+ 2 trang tùy chọn).

| Trang | `page_name` | Vai trò | Module | Khung Stitch | Dữ liệu hiện tại |
|---|---|---|---|---|---|
| Đăng nhập / Đăng ký | (view-auth) | Khách | `ui/pages/login.py` | `ng_nh_p_ng_k_emovoice_desktop` | — (service chưa cài: hiện thông báo) |
| Quên mật khẩu | (view-auth, panel 3) | Khách | `ui/pages/login.py` | **chưa có** (dựng theo style Stitch) | — |
| Phân tích mới (3 trạng thái) | `analyze` | User, Admin | `ui/pages/analyze.py` | `ph_n_t_ch_c_m_x_c_nh_p_m_thanh` + `k_t_qu_ph_n_t_ch_c_m_x_c_xai`; trạng thái "đang xử lý" **chưa có** | Kết quả mẫu cứng |
| Lịch sử phân tích + drawer | `history` | User, Admin | `ui/pages/history.py` | `l_ch_s_ph_n_t_ch_c_m_x_c` | 48 bản ghi mẫu cứng |
| Mô hình & hiệu năng | `models` | User, Admin | `ui/pages/model_performance.py` | `m_h_nh_hi_u_n_ng_ai` | **Đọc `assets/metrics/*.json`** |
| Tổng quan (admin) | `admin_overview` | Admin | `ui/pages/admin_overview.py` | `qu_n_tr_h_th_ng_emovoice` (phần KPI, biểu đồ, trạng thái) | KPI mẫu + mô hình đang dùng từ JSON |
| Quản lý người dùng (admin) | `admin_users` | Admin | `ui/pages/admin_users.py` | `qu_n_tr_h_th_ng_emovoice` (phần bảng người dùng) | 23 tài khoản mẫu |
| Nhật ký hệ thống (admin) | `admin_logs` | Admin | `ui/pages/admin_logs.py` | `qu_n_tr_h_th_ng_emovoice` (chỉ có thẻ timeline) | 30 dòng mẫu |
| Quản lý mô hình AI (admin) | `admin_models` | Admin | `ui/pages/admin_models.py` | **chưa có** | Đọc JSON; đổi mô hình chưa cài |
| Quản lý dữ liệu âm thanh (admin) | `admin_audio` | Admin | `ui/pages/admin_audio.py` | **chưa có** | 30 mẫu giả |

Hai trang admin cuối chỉ được dựng khi `ENABLE_ADMIN_EXTRA_PAGES=1`. Stitch chỉ có **một** trang admin gộp (tổng quan + người dùng + nhật ký) nên ba trang admin đã được tách ra từ đó.

## Trang Phân tích mới — 3 trạng thái

| Trạng thái | Nội dung | Thành phần |
|---|---|---|
| 1. Nhập âm thanh | `gr.Tabs` "Tải tệp lên" (`gr.Audio(sources=["upload"], type="filepath")`) và "Thu âm trực tiếp" (`sources=["microphone"]`); chip tiền xử lý; nút "Thực hiện phân tích cảm xúc"; panel chẩn đoán lỗi bên phải | `Column col_input`, `gr.HTML` (chips, toast) |
| 2. Đang xử lý | Danh sách bước (nạp/resample, cắt lặng, chuẩn hóa/cố định 3 s, suy luận, tạo XAI) | `Column col_processing`, `processing_checklist.html` |
| 3. Kết quả | Nút "Phân tích tệp khác"/"Tải ảnh kết quả"; hero kết quả; 8 thanh xác suất; heatmap XAI 5 mức rời rạc + vạch kết thúc giọng nói; banner độ tin cậy thấp | `Column col_result`, `emotion_hero.html`, `emotion_bars.html`, `heatmap_strip.html`, `banner.html` |

Stepper 4 bước (`stepper.html`) đổi theo trạng thái. Phụ đề bước 3 ghi "DistilHuBERT + LoRA" (Stitch ghi "CRNN/Wav2Vec", bước 4 ghi "SHAP" — không đúng với báo cáo).

## Điều hướng và phân quyền

- Sidebar (user): Phân tích cảm xúc, Lịch sử phân tích, Mô hình & hiệu năng. Admin thêm nhóm **QUẢN TRỊ HỆ THỐNG**; người thường không thấy nhóm này (Column ẩn, chỉ bật khi `SessionUser.is_admin`).
- `show_page` chặn trang admin với người thường; mọi handler admin gọi `guard_admin` (xem [architecture.md](architecture.md) mục 4). Đây là lý do `build()` của trang admin chỉ tạo khung rỗng: dữ liệu nạp qua `load_fn` sau khi qua `require_admin`.
- `DEV_BYPASS_LOGIN=1` hiện hai nút "Vào thử" (User/Admin) ở trang đăng nhập để xem giao diện; handler kiểm tra lại cờ ở server. **Tắt khi triển khai.**

## Chỗ Gradio không dựng y hệt Stitch

| Khối Stitch | Cách mô phỏng trong Gradio | Khác biệt còn lại |
|---|---|---|
| Sidebar cố định 260px + topbar 64px | `Column#ev-sidebar` (sticky, 100vh) + `gr.HTML#ev-topbar` (sticky) | Khung cuộn theo trang Gradio, không phải `position: fixed` thật |
| Mục menu có icon, số đếm (12), nhãn "Admin" | `gr.Button` + CSS `::before` (ligature Material Symbols) | Không có badge số/"Admin" |
| Ô nhập có icon trái, nút hiện/ẩn mật khẩu | `gr.Textbox` + CSS | Không có icon trong ô; ô mật khẩu không có nút hiện/ẩn |
| Segmented tabs Đăng nhập/Đăng ký | 2 `gr.Button` + 3 `Column(visible)` (đăng nhập/đăng ký/quên mật khẩu) | Chuyển panel không có hiệu ứng |
| Vùng kéo thả tùy biến (icon mây, chip tên tệp/dung lượng/thời lượng) | `gr.Audio(sources=["upload"])` + CSS viền đứt | Giao diện upload và chip tệp do Gradio quyết định |
| Trình phát sóng âm rời rạc (play, lặp, âm lượng) | Trình phát waveform của `gr.Audio` | Không có thanh sóng rời rạc, không có nút lặp/âm lượng riêng |
| Thu âm: nút đỏ nhấp nháy, đồng hồ 00:02.8, VU meter rời rạc | Micro mặc định của `gr.Audio(sources=["microphone"])` | Không có VU meter, đồng hồ lớn, nút Hủy/Dừng theo Stitch |
| Panel "Chẩn đoán & trạng thái lỗi" (3 toast mẫu) | `gr.HTML` toast phẳng, nội dung đổi theo lỗi thật | Lỗi hệ thống khác dùng toast của Gradio (`gr.Error`/`gr.Warning`), không đổi được skin hoàn toàn |
| Hero kết quả, thanh xác suất, heatmap ô rời rạc, KPI, hàng trạng thái, empty state, stepper | `gr.HTML` + `ui/templates/*.html` + CSS thuần (`ui/css/components.css`) | Gần y hệt (đây là các khối dựng sát nhất); tooltip độ tin cậy dùng thuộc tính `title` |
| Bảng lịch sử tùy biến (chip, thanh tin cậy, nút "Nghe lại"/"Xem XAI" trên từng dòng) | `gr.Dataframe` với `datatype="html"`; chọn dòng → mở drawer | Không tô được dòng đang chọn, không có nút trong từng dòng, header không dính |
| Drawer chi tiết cột phải sticky luôn hiện | `Column(visible)` bật khi chọn dòng + nút "Đóng bảng" | Chỉ hiện sau khi chọn dòng; không dính khi cuộn |
| Phân trang (số dòng/trang, Trước/Sau, số trang, "…") | `components/pagination.py`: `gr.State` + `gr.Button` + `gr.Dropdown` | Tối đa 5 nút số, không có "…" |
| Công tắc bật/tắt tài khoản trong bảng | Chọn dòng + nút "Khóa / mở khóa tài khoản đã chọn" | Không có switch trong từng dòng |
| Biểu đồ cột/donut SVG phẳng ở admin | `plotly` (`components/charts.py`) với màu phẳng theo bảng màu | Phông và tooltip theo plotly |
| `<select>` có icon | `gr.Dropdown` | Kiểu combobox của Gradio |
| Logo và avatar là ảnh ngoài (googleusercontent) | Icon `graphic_eq` + avatar chữ cái đầu | Không có ảnh |
| Icon Material Symbols và font Be Vietnam Pro / Inter | Nạp từ Google Fonts qua `head` | **Cần Internet**: offline icon hiện thành chữ ligature. TODO tự lưu font cục bộ |
| Responsive: rail 72px (tablet), thanh dưới (mobile) | CSS `@media (max-width: 1100px)` thu sidebar còn rail biểu tượng | Chưa làm thanh điều hướng dưới cho mobile |
| Ẩn thanh cuộn, dark class của Tailwind | Không áp dụng; dark mode **tắt hẳn** (`?__theme=light` + token theme) | — |
