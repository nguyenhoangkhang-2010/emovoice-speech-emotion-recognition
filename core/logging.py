# Cấu hình ghi nhật ký ra tệp logs/emovoice.log (cùng lúc vẫn in ra console).
# Bảng system_logs (services/audit_service) là nhật ký NGHIỆP VỤ cho admin xem trên giao diện; tệp này là nhật ký KỸ THUẬT:
# gồm mọi logger.* trong code, nhất là traceback của lỗi (CSDL không lưu), và vẫn đọc được khi CSDL không kết nối được.
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from core.config import settings

LOG_FILE = "emovoice.log"
MAX_BYTES = 2 * 1024 * 1024  # xoay tệp khi đầy 2 MB, giữ 5 bản cũ: tối đa ~12 MB trên đĩa
BACKUPS = 5
FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
NOISY = ("httpx", "httpcore", "urllib3", "matplotlib", "numba", "multipart", "PIL", "asyncio")  # thư viện bên thứ ba nói nhiều ở mức INFO/DEBUG

_MARK = "_emovoice_handler"


def setup_logging(log_dir: Optional[Path] = None, level: int = logging.INFO) -> Optional[Path]:
    """Gắn tệp nhật ký (có xoay vòng) và console vào root logger. Gọi nhiều lần vẫn chỉ gắn một lần.
    Trả về đường dẫn tệp log, hoặc None nếu không ghi được tệp (khi đó vẫn chạy bình thường, chỉ còn console)."""
    root = logging.getLogger()
    for handler in list(root.handlers):  # gọi lại thì thay cấu hình cũ, không nhân đôi dòng
        if getattr(handler, _MARK, False):
            root.removeHandler(handler)
            handler.close()
    root.setLevel(level)
    formatter = logging.Formatter(FORMAT)

    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(formatter)
    setattr(console, _MARK, True)
    root.addHandler(console)

    path: Optional[Path] = None
    try:
        directory = Path(log_dir) if log_dir is not None else settings.log_dir
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / LOG_FILE
        file_handler = RotatingFileHandler(path, maxBytes=MAX_BYTES, backupCount=BACKUPS, encoding="utf-8")
        file_handler.setFormatter(formatter)
        setattr(file_handler, _MARK, True)
        root.addHandler(file_handler)
    except OSError:  # thư mục chỉ đọc, hết dung lượng...: ghi nhật ký là việc phụ, không được làm ứng dụng không khởi động được
        path = None
        logging.getLogger(__name__).exception("Không mở được tệp nhật ký, chỉ ghi ra console")

    for name in NOISY:
        logging.getLogger(name).setLevel(logging.WARNING)
    return path
