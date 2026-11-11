# Bản sao tệp để nút "Tải về" cho ra đúng tên tệp gốc: tệp lưu trên máy chủ chỉ có tên ngẫu nhiên (uuid).
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Optional


def export_dir() -> Path:
    path = Path(tempfile.gettempdir()) / "emovoice_exports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_name(name: object, suffix: str = "") -> str:
    """Tên tệp an toàn để lưu: bỏ đường dẫn và ký tự lạ (tên do người dùng đặt), giữ chữ có dấu; thiếu đuôi thì thêm `suffix`."""
    base = re.sub(r"[^\w.\- ()]+", "_", Path(str(name or "")).name).strip(" .") or "audio"
    return base + suffix if suffix and not Path(base).suffix else base


def audio_copy(src: Optional[str], display_name: object, folder: str, base_dir: Optional[Path] = None) -> Optional[str]:
    """Sao tệp âm thanh `src` vào <base_dir>/<folder>/<tên gốc>; None nếu tệp không còn. `folder` riêng cho từng bản ghi để tên không trùng nhau."""
    if not src or not os.path.exists(src):
        return None
    target_dir = Path(base_dir or export_dir()) / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / safe_name(display_name, Path(src).suffix)
    shutil.copyfile(src, target)
    return str(target)
