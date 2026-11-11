# Xóa dữ liệu âm thanh: dòng trong CSDL (một giao dịch) rồi tệp trên đĩa (chỉ sau khi giao dịch thành công).
# Dùng chung cho admin xóa mẫu / xóa tài khoản (admin_service) và người dùng tự xóa lịch sử của mình (history_service).
from pathlib import Path
from typing import List, Optional

from core.config import settings
from models.audio_file import AudioFile


def drop_audio(db, audio: AudioFile) -> List[Optional[str]]:
    """Xóa khỏi CSDL (chưa commit) một mẫu cùng lượt phân tích, điểm số và đặc trưng; trả đường dẫn các tệp liên quan để xóa sau khi giao dịch thành công."""
    paths = [audio.file_path, *(p.heatmap_path for p in audio.predictions)]
    if audio.features is not None:
        paths.append(audio.features.mel_image_path)
    for prediction in list(audio.predictions):
        db.delete(prediction)
    db.delete(audio)
    return paths


def remove_stored_file(path: Optional[str], allowed_dirs: List[Path]) -> bool:
    """Xóa một tệp CHỈ khi nó nằm trong thư mục lưu trữ của ứng dụng (đường dẫn trong CSDL không được tin tuyệt đối). Trả True nếu đã xóa."""
    if not path:
        return False
    try:
        target = Path(path).resolve()
        if not any(base.resolve() in target.parents for base in allowed_dirs):
            return False
        target.unlink()
        return True
    except OSError:  # tệp đã mất hoặc đang bị khóa: bỏ qua, dòng trong CSDL vẫn được xóa
        return False


def remove_files(paths: List[Optional[str]]) -> int:
    """Xóa các tệp âm thanh, ảnh XAI, ảnh Mel trong kho của ứng dụng; trả số tệp đã xóa."""
    allowed = [settings.upload_dir, settings.heatmap_dir, settings.mel_dir]
    return sum(remove_stored_file(p, allowed) for p in paths)
