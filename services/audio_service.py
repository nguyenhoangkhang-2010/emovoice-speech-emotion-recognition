# UC02 (báo cáo Bảng 2.4): kiểm tra hợp lệ và lưu tệp âm thanh tải lên hoặc thu âm.
# Tệp lưu vào storage/uploads với tên uuid (không tin tên tệp client); tên gốc chỉ ghi vào cột filename để hiển thị.
import os
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from core.config import settings
from core.session import SessionUser, require_login
from db.session import get_session
from models.audio_file import AudioFile

MSG_FORMAT = "Định dạng không được hỗ trợ, vui lòng chọn WAV hoặc MP3."  # UC02-E1 (khung Stitch)
MSG_MISSING = "Không tìm thấy tệp âm thanh đã chọn."
MSG_EMPTY = "Tệp âm thanh rỗng hoặc không có nội dung."
MSG_TOO_BIG = "Tệp quá lớn, dung lượng tối đa là {max_mb} MB."
MSG_UNREADABLE = "Không giải mã được tệp âm thanh, tệp có thể bị hỏng."


def _duration(file_path: str) -> float:
    """Thời lượng (giây) của tệp; ValueError nếu không giải mã được."""
    try:
        import soundfile as sf

        return float(sf.info(file_path).duration)
    except Exception:
        pass
    try:  # MP3 và vài định dạng libsndfile bản cũ không đọc được
        import librosa

        return float(librosa.get_duration(path=file_path))
    except Exception as exc:
        raise ValueError(MSG_UNREADABLE) from exc


def validate_upload(file_path: str) -> float:
    """Kiểm tra đuôi tệp (ALLOWED_AUDIO), dung lượng (MAX_UPLOAD_MB) và giải mã thử. Trả thời lượng giây; sai thì ValueError."""
    if not file_path or not os.path.isfile(file_path):
        raise ValueError(MSG_MISSING)
    if Path(file_path).suffix.lower().lstrip(".") not in settings.allowed_audio_list:
        raise ValueError(MSG_FORMAT)
    size = os.path.getsize(file_path)
    if size == 0:
        raise ValueError(MSG_EMPTY)
    if size > settings.max_upload_bytes:
        raise ValueError(MSG_TOO_BIG.format(max_mb=settings.max_upload_mb))
    duration = _duration(file_path)
    if duration <= 0:
        raise ValueError(MSG_EMPTY)
    return duration


def _to_dict(row: AudioFile) -> Dict[str, Any]:
    return {
        "audio_id": row.audio_id,
        "user_id": row.user_id,
        "filename": row.filename,
        "file_path": row.file_path,
        "duration": row.duration,
        "uploaded_at": row.uploaded_at,
    }


def save_upload(session: SessionUser, file_path: str) -> Optional[Dict[str, Any]]:
    """Kiểm tra rồi chép tệp vào storage/uploads (tên uuid) và tạo dòng audio_files.
    Trả None với phiên "Vào thử" (không có dòng trong users nên không có khóa ngoại để lưu)."""
    user = require_login(session)
    duration = validate_upload(file_path)
    if user.is_demo:
        return None
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    stored = settings.upload_dir / f"{uuid.uuid4().hex}{Path(file_path).suffix.lower()}"
    shutil.copyfile(file_path, stored)
    try:
        with get_session() as db:
            row = AudioFile(user_id=user.user_id, filename=os.path.basename(file_path)[:255], file_path=str(stored), duration=duration)
            db.add(row)
            db.commit()
            return _to_dict(row)
    except Exception:
        stored.unlink(missing_ok=True)  # không để lại tệp mồ côi khi ghi DB lỗi
        raise


def get_audio_for_user(session: SessionUser, audio_id: int) -> Optional[Dict[str, Any]]:
    """Mẫu âm thanh nếu thuộc người dùng này (Admin xem được mọi mẫu); None nếu không có hoặc của người khác."""
    user = require_login(session)
    with get_session() as db:
        row = db.get(AudioFile, audio_id)
        if row is None or (row.user_id != user.user_id and not user.is_admin):
            return None
        return _to_dict(row)
