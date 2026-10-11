# UC02 (báo cáo Bảng 2.4): kiểm tra hợp lệ và lưu tệp âm thanh tải lên hoặc thu âm.
from core.session import SessionUser


def validate_upload(file_path: str) -> None:
    raise NotImplementedError(
        "TODO UC02: kiểm tra đuôi tệp (ALLOWED_AUDIO), dung lượng (MAX_UPLOAD_MB), giải mã thử; "
        "thông báo lỗi theo khung Stitch: 'Định dạng không được hỗ trợ, vui lòng chọn WAV hoặc MP3.' (UC02-E1)"
    )


def save_upload(session: SessionUser, file_path: str):
    raise NotImplementedError("TODO UC02: copy vào storage/uploads với tên uuid (không tin tên tệp client), tạo dòng audio_files")


def get_audio_for_user(session: SessionUser, audio_id: int):
    raise NotImplementedError("TODO: trả audio nếu thuộc user; Admin dùng admin_service.list_all_audio")
