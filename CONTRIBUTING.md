# Quy ước làm việc nhóm

Nhóm 3 sinh viên (Trần Nhã Phương, Nguyễn Hoàng Khang, Lê Dư Bảo Khang). Đề cương yêu cầu gặp GVHD ít nhất 1 lần/tuần và **trước mỗi buổi báo cáo phải tích hợp các phần được phân công vào chung một tài liệu/phần mềm** — vì vậy mỗi người làm trên một module riêng, ít chạm file của nhau, và nhánh `main` luôn phải chạy được `python app.py`.

## Chia việc theo module

| Module | Phạm vi | Gợi ý người phụ trách (nhóm tự chốt) |
|---|---|---|
| `ml/` | Port từ `ser_project`: tiền xử lý, mô hình, suy luận, XAI, đánh giá, benchmark, dataset | Người A (ML) |
| `services/` + `models/` + `db/` + `core/` | Xác thực, quên mật khẩu, lưu tệp/dự đoán, lịch sử, quản trị, CSDL | Người B (nghiệp vụ + dữ liệu) |
| `ui/` | Trang Gradio, CSS/template theo Stitch, đối chiếu giao diện | Người C (giao diện) |
| `docs/`, `tests/`, báo cáo | Viết chung; mỗi người cập nhật phần của mình | Cả nhóm |

Ranh giới giữa các module là chữ ký hàm trong `services/` và `ml/`: **không đổi tên hàm hoặc tham số đã có** khi chưa báo nhóm (`load_and_preprocess_audio`, `pad_or_truncate_waveform`, `TemporalAttentionPooling`, `DistilHuBERTForSER`, các hàm trong `services/`). Cần đổi thì sửa cả nơi gọi trong cùng một PR.

## Nhánh

- `main`: luôn chạy được, là bản dùng cho buổi báo cáo.
- `feat/<module>-<việc>` (ví dụ `feat/ml-port-preprocess`, `feat/services-auth`, `feat/ui-history-drawer`), `fix/<module>-<lỗi>`, `docs/<chủ đề>`.
- Mở PR vào `main`, ít nhất 1 thành viên khác xem trước khi gộp. Gộp bằng *squash*.
- **Trước mỗi buổi báo cáo (hạn: 1 ngày):** mọi nhánh đã gộp, `python app.py` chạy, cập nhật `docs/outline-traceability.md` (cột Trạng thái) và `docs/roadmap.md`.

## Commit

Dạng `<loại>(<module>): <mô tả ngắn, tiếng Việt hoặc tiếng Anh>`, các loại: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`.

```
feat(services): cài đặt auth_service.register với bcrypt
fix(ui): sửa phân trang lịch sử khi bộ lọc không có kết quả
docs(traceability): cập nhật trạng thái UC01
```

Mỗi commit một việc; không commit `.env`, `*.db`, `ml/weights/*.pt`, nội dung `storage/` và `logs/` (đã có trong `.gitignore`).

## Quy tắc code

1. Chuỗi hiển thị tiếng Việt chỉ đặt trong `ui/i18n_vi.py`; tên file/biến bằng tiếng Anh.
2. Màu và bo góc chỉ dùng token trong `ui/css/tokens.css`. **Không dùng màu đen, `#000`, `rgba(0,0,0,…)` hay gradient.** Chạy lệnh quét ở `docs/stitch-mapping.md` mục 3 trước khi gộp thay đổi CSS/HTML.
3. Mọi hàm admin trong `services/admin_service.py` và mọi handler trong `ui/pages/admin_*.py` phải gọi `guard_admin`/`require_admin` ở dòng đầu. Ẩn menu chỉ là UX.
4. Số liệu mô hình trên giao diện đọc từ bảng `models` (ghi bởi `python -m ml.register_model` sau khi đánh giá mô hình thật), không hard-code trong `ui/` và không chép tay vào mã.
5. Mỗi TODO phải nêu rõ việc cần làm và mục báo cáo/đề cương liên quan, không viết TODO mơ hồ.
6. Thêm thư viện: báo nhóm và cập nhật `requirements.txt` (Captum là tùy chọn, chưa thêm).
7. Mỗi chức năng mới đi kèm test trong `tests/` (hoặc cập nhật ca trong `docs/test-plan.md`).

## Kiểm tra trước khi tạo PR

```powershell
python -m compileall -q core db models services ml ui tests app.py
python -m pytest tests
python app.py        # đăng nhập (hoặc DEV_BYPASS_LOGIN=1), bấm qua các trang
```
