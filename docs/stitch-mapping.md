# Đối chiếu Stitch → Gradio

Nguồn: `stitch/DESIGN.md` ("Clarity Audio Intelligence") và 7 cặp `stitch/images/*.png` + `stitch/html/*.html` (bản sao nguyên bản, không chỉnh). Mọi giá trị dưới đây rút từ các file này, không đoán.

## 1. Bảng ánh xạ file Stitch → trang → module → component

| File Stitch (png/html) | Trang | Module `ui/pages` | Component Gradio | Template HTML |
|---|---|---|---|---|
| `ng_nh_p_ng_k_emovoice_desktop` | Đăng nhập, Đăng ký | `login.py` | `gr.Row#auth-body` (2 cột 50/50), `gr.Button` segmented, `gr.Textbox`, `gr.Checkbox` | `login_navbar.html`, `login_hero.html` |
| *(chưa có Stitch)* | Quên mật khẩu | `login.py` (panel 3) | `gr.Textbox`, `gr.Button`, 2 `Column(visible)` (bước 1/2) | — (dựng theo style của khung đăng nhập) |
| `ph_n_t_ch_c_m_x_c_nh_p_m_thanh` | Phân tích mới — nhập âm thanh | `analyze.py` (`col_input`) | `gr.Tabs/Tab`, `gr.Audio` ×2, `gr.Button`, `gr.HTML` | `stepper.html`, `toast.html` |
| *(chưa có Stitch)* | Phân tích mới — đang xử lý | `analyze.py` (`col_processing`) | `gr.HTML` | `processing_checklist.html`, `stepper.html` |
| `k_t_qu_ph_n_t_ch_c_m_x_c_xai` | Phân tích mới — kết quả | `analyze.py` (`col_result`) | `gr.Row` + 4 `gr.HTML`, `gr.Button` | `emotion_hero.html`, `emotion_bars.html`, `heatmap_strip.html`, `banner.html` |
| `l_ch_s_ph_n_t_ch_c_m_x_c` | Lịch sử + drawer | `history.py` | `gr.Dataframe(datatype="html")`, `gr.Textbox`, `gr.Dropdown`, `Column(visible)` drawer, `gr.Audio` | `page_header.html`, `empty_state.html` + hàm `render.*_html` (chip, thanh tin cậy, heatmap mini) |
| `m_h_nh_hi_u_n_ng_ai` | Mô hình & hiệu năng | `model_performance.py` | 8 `gr.HTML`, `gr.Dropdown` (chọn mô hình cho ma trận) | `page_header.html` + `render.model_hero_html`, `comparison_bars_html`, `models_table_html`, `confusion_matrix_html`, `insight_html` |
| `qu_n_tr_h_th_ng_emovoice` (KPI, biểu đồ, hạ tầng) | Admin Tổng quan | `admin_overview.py` | 7 `gr.HTML`, 2 `gr.Plot` | `kpi_card.html`, `status_row.html` |
| `qu_n_tr_h_th_ng_emovoice` (bảng người dùng) | Admin Quản lý người dùng | `admin_users.py` | `gr.Dataframe`, `gr.Textbox`, `gr.Button` | `page_header.html` |
| `qu_n_tr_h_th_ng_emovoice` (timeline "Nhật ký hoạt động") | Admin Nhật ký hệ thống | `admin_logs.py` | `gr.Dataframe`, `gr.Dropdown`, `gr.Textbox` | `page_header.html` |
| *(chưa có Stitch)* | Admin Quản lý mô hình AI | `admin_models.py` | `gr.HTML`, `gr.Dropdown`, `gr.Button` | `page_header.html` |
| *(chưa có Stitch)* | Admin Quản lý dữ liệu âm thanh | `admin_audio.py` | `gr.Dataframe`, `gr.Audio`, `gr.Button` | `page_header.html` |
| `clarity_audio_intelligence/DESIGN.md` + `emovoice_design_system_component_library` | Hệ thống thiết kế (không phải trang) | — | `ui/css/tokens.css`, `ui/theme.py` | — |
| Sidebar user / sidebar admin (có trong 6 file app) | Khung ứng dụng | `components/sidebar.py`, `components/topbar.py` | `gr.Column#ev-sidebar`, `gr.Button`, `gr.HTML#ev-topbar` | `sidebar_brand.html`, `sidebar_user.html`, `topbar.html` |

Các biến thể sidebar: bản user có 2 nhóm (*Tác vụ phân tích*; *Học máy & Tài nguyên*); bản admin trong Stitch gộp mọi mục vào một danh sách kèm nhãn "Admin". Theo yêu cầu dự án, skeleton dùng nhóm riêng **QUẢN TRỊ HỆ THỐNG** chỉ dựng cho Admin.

## 2. Token rút từ HTML/DESIGN.md

**Bảng màu** (DESIGN.md trùng khớp 100% với bảng màu chuẩn của dự án, nên không có điểm lệch):

| Token | Giá trị | Token | Giá trị |
|---|---|---|---|
| Nền (canvas) | `#F4F6FB` | Primary | `#4361D8` |
| Thẻ | `#FFFFFF` | Primary hover | `#3047B0` |
| Bề mặt phụ | `#EEF1F8` | Primary tint | `#E8EDFC` |
| Viền | `#DCE2F0` | Primary tint 2 | `#C5D1F7` |
| Chữ tiêu đề | `#2F3E63` | Success/teal | `#1FA89A` |
| Chữ thân | `#4A5878` | Warning | `#E9A23B` |
| Chữ phụ | `#7A88A6` | Error | `#DC5A5A` |

**8 cảm xúc**: neutral `#8C9BB8`, calm `#5BB5C6`, happy `#F2C14E`, sad `#6A88D7`, angry `#E5675B`, fearful `#9A82C9`, disgust `#84B26B`, surprised `#F29A52`. **Heatmap 5 mức** (DESIGN.md, trang kết quả, trang mô hình): `#E8EDFC`, `#C5D1F7`, `#9DB1F0`, `#6F89E6`, `#4361D8`.

**Font**: Be Vietnam Pro 400/500/600/700 (tiêu đề), Inter 400/500/600 (thân, số liệu `tnum`), Material Symbols Outlined (icon). Thang chữ: display 36/44 (700, −0.02em); headline-lg 28/36 (700); headline-md 22/30 (600); headline-sm 18/26 (600); body-lg 18/28; body-md 16/24; body-sm 14/20; label-lg 14/20 (600); label-md 12/16 (500); label-sm 11/14 (600, +0.04em).

**Hình khối**: thẻ/panel 16px; nút, ô nhập, dropdown 12px; badge/ô heatmap 6–8px; chip cảm xúc và nút thu âm pill 9999px. **Khoảng cách** lưới 8px: xs 4, sm 8, md 16, lg 24 (gutter), xl 32 (margin). **Khung**: sidebar 260px, topbar 64px (cố định); trang đăng nhập: navbar 72px, 2 cột bằng nhau, thẻ đăng nhập rộng 440px, padding 36px, ô nhập cao 48px, nút CTA 48px (đăng nhập) / 52px (phân tích). **Bóng** pha màu primary: L1 `0 2px 8px rgba(67,97,216,.04)`, L2 `0 8px 24px … .08`, L3 `0 16px 36px … .12`; thẻ đăng nhập `0 8px 24px rgba(67,97,216,.06)`; thẻ hero mô hình `0 4px 16px rgba(67,97,216,.08)`. **Nút**: primary nền `#4361D8` chữ trắng (hover `#3047B0`); tinted nền `#E8EDFC` chữ primary (hover `#C5D1F7`); outline viền `#DCE2F0` nền trắng (hover `#EEF1F8`); danger `#DC5A5A`. **Chip cảm xúc**: pill, chấm 6–10px + nền màu cảm xúc độ mờ 15–20%, chữ `#2F3E63`. **Bảng**: header nền bề mặt phụ, chữ hoa 11px, phân cách hàng 1px; **phân trang**: nút 32×32, "Trước/Sau", chọn 10/20/50 dòng. **Stepper**: vòng 32px, đường nối 2px × 32px, bước hiện tại có vòng sáng 4px.

## 3. Kiểm tra màu đen và gradient

**Kết quả quét 7 file HTML** (đã loại phần định nghĩa token trong cấu hình Tailwind, chỉ đếm chỗ dùng):

| Phát hiện | Nơi xuất hiện (số lần theo file) | Thay bằng |
|---|---|---|
| Không có `#000`, `black`, `rgb(0,0,0)`, `#111`, `gradient`, `blur` ở dạng giá trị. Từ "blur", "gradient" chỉ nằm trong **chú thích** HTML của trang admin | admin 2 | — |
| `text-on-surface` = `#181C20` (gần đen): 1 lần ở `<body>` (màu chữ mặc định) + `hover:text-on-surface` ở mục menu/nút | kết quả 1+4, lịch sử 1+4, mô hình 1+4, phân tích 1+10, admin 1+6 | `#2F3E63` (tiêu đề) / `#4A5878` (thân) |
| `selection:text-on-secondary-fixed` = `#081A3D` (xanh navy gần đen) làm màu chữ khi bôi chọn | 1 mỗi trang app (5 trang) | `#2F3E63` |
| `hover:bg-on-primary-fixed-variant` = `#1139B2` (xanh đậm, không đen) cho nút primary hover ở trang mô hình và admin | mô hình 1, admin 1 | `#3047B0` (primary hover chuẩn) |
| Tailwind `shadow-sm/md/lg` mặc định = `rgb(0 0 0 / 5–10%)` (bóng đen) | thiết kế 2, kết quả 8, lịch sử 7, đăng nhập 1, phân tích 9, admin 11 | Bóng pha primary L1/L2 (≤ 8%): `rgba(67,97,216,…)` |
| `#BA1A1A` (đỏ sẫm của Material) thay vì error `#DC5A5A` | kết quả 1, lịch sử 1, mô hình 1, phân tích 11, admin 3 | `#DC5A5A` |

Kết quả quét CSS/HTML/Python của skeleton mới (`ui/`, `app.py`, `assets/`): **không có** màu đen, `rgba(0,0,0,…)` hay gradient; mọi `rgba` dùng nền `67,97,216` (primary) hoặc màu cảm xúc/teal với độ mờ ≤ 20%. Màu duy nhất ngoài bảng chuẩn là 4 nấc xám-xanh cho `neutral_hue` của theme Gradio (`#C5CCE0`, `#A3AFCB`, `#6A7899`, `#3B4A6E`, nội suy giữa `#DCE2F0` và `#2F3E63`) và 3 nền cảnh báo lấy nguyên từ Stitch (`#FEF7EC`, `#FCE8CA`, `#FDECEB`).

Lệnh quét (chạy từ `emovoice/`, kỳ vọng không có dòng nào ngoài chú thích):

```bash
grep -rniE "#000|#000000|rgba?\(\s*0\s*,\s*0\s*,\s*0|black|#111|gradient|backdrop|blur\(|drop-shadow" ui app.py assets --include=*.css --include=*.html --include=*.py --include=*.json
```

> Cần kiểm tra bằng mắt khi chạy thật: CSS mặc định của Gradio (icon, dropdown, trình phát audio) có thể còn dùng biến màu tối; theme + `tokens.css` đã ghi đè các biến chính nhưng chưa thể kiểm chứng vì gradio chưa được cài trong môi trường này.

## 4. Chỗ Stitch tự mâu thuẫn hoặc lệch báo cáo (đã xử lý thế nào)

| Điểm lệch | Xử lý trong skeleton |
|---|---|
| HTML dùng token Material (primary `#2547BE`, mục menu active `#C2D1FE`/`#DAE2FF`, chữ `#4F5E84`) khác DESIGN.md/bảng màu chuẩn (`#4361D8`, `#E8EDFC`, `#4A5878`) | Dùng **DESIGN.md/bảng màu chuẩn** (nhất quán giữa các trang) |
| Bo góc thẻ: trang phân tích/lịch sử/admin dùng `rounded-xl` = 12px (do cấu hình Tailwind), trang kết quả/mô hình dùng `rounded-2xl` = 16px; DESIGN.md quy định 16px | 16px cho mọi thẻ |
| Bậc heatmap lịch sử `#8AA4F0`, `#6080E4` khác DESIGN.md `#9DB1F0`, `#6F89E6` | Dùng bậc DESIGN.md |
| Thanh "Ghê tởm" ở lịch sử dùng `#4F5E84` thay vì màu disgust `#84B26B` | Dùng màu cảm xúc chuẩn |
| Nhãn lệch báo cáo: "Lo sợ", "Ghê tởm", "Bình thản" (lịch sử); "Khinh bỉ", "Hào hứng" (donut admin) | Dùng 8 nhãn của báo cáo: Sợ hãi, Chán ghét, Êm đềm…; donut admin quy về 8 lớp |
| Donut admin dùng màu ngoài token cảm xúc (`#747685`, `#E0A32B`, `#BA1A1A`, `#00796E`…) | `charts.py` dùng đúng màu cảm xúc |
| Trang mô hình tự đặt số: HuBERT 74,10%, wav2vec 2.0 71,80%, SVM 54,80%, RF 14,5 MB/3,10 ms/49,10%, "Test 480 mẫu", "5-Fold CV", "RAVDESS-VN", "INT8 ONNX", "Checkpoint epoch-48" | **Không dùng**; số liệu đọc từ `assets/metrics` (RF 52,22/48,11/0,09 ms; test 180 mẫu; chưa Pruning/lượng tử hóa); HuBERT/wav2vec 2.0 gốc hiện "Chưa đo" |
| Ma trận nhầm lẫn trong Stitch là số bịa (đường chéo 65–85%) | Dùng ma trận dựng từ Bảng 5.2/Hình 4.2 (đường chéo 132/180) |
| Stepper ghi "CRNN/Wav2Vec", "Giải thích SHAP"; chip "Bộ mã hóa tiếng Việt v2.4"; tên "Phân tích biểu cảm hội thoại" | "DistilHuBERT + LoRA", "Biểu đồ chú ý"; bỏ chip phiên bản bịa |
| Admin Stitch: API Gateway/NGINX, GPU T4, PostgreSQL/Vector DB, 2FA, "huấn luyện lại LoRA adapter v2.1" | Hàng trạng thái dùng 3 dịch vụ thật: Ứng dụng Gradio, Mô hình AI, Cơ sở dữ liệu |
| Số thập phân kiểu Anh ("87.4%") trong Stitch | Giữ kiểu Stitch cho hero/bảng; báo cáo dùng dấu phẩy — cần người quyết định thống nhất |
| Nền cảnh báo độ tin cậy thấp: chữ `#E9A23B` trên `#FEF7EC` (tương phản thấp) | Chữ tiêu đề `#2F3E63`, giữ nền/viền cảnh báo của Stitch (DESIGN.md yêu cầu WCAG AA) |
