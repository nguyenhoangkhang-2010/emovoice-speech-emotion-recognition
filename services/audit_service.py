# Ghi sự kiện vào nhật ký hệ thống (bảng system_logs) cho admin theo dõi: phân tích, lỗi, tệp bị từ chối, nạp mô hình...
# Ghi nhật ký là việc PHỤ: không bao giờ được làm hỏng thao tác của người dùng, nên log() nuốt mọi lỗi (chỉ ghi ra console).
# Những chỗ đã có giao dịch CSDL riêng (đăng nhập, khóa tài khoản, xóa mẫu...) thêm dòng SystemLog ngay trong giao dịch đó để ghi cùng lúc với thay đổi.
# KHÔNG ghi mật khẩu, mã đặt lại, nội dung âm thanh hay giá trị hồ sơ; chỉ ghi tên tệp, tên tài khoản, nhãn kết quả, thời gian.
import logging
import re
from typing import Optional, Union

from core.session import SessionUser
from db.session import get_session
from models.system_log import SystemLog

logger = logging.getLogger(__name__)

LEVELS = ("INFO", "WARNING", "ERROR")
MESSAGE_MAX = 500
_CONTROL = re.compile(r"[\x00-\x1f\x7f  ]+")


def clean(text: object, limit: int = MESSAGE_MAX) -> str:
    """Một dòng sạch: ký tự điều khiển và xuống dòng thành dấu cách (tên tệp do người dùng đặt không được làm vỡ dòng nhật ký), cắt bớt nếu quá dài."""
    value = _CONTROL.sub(" ", str(text)).strip()
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _user_id(user: Union[SessionUser, int, None]) -> Optional[int]:
    uid = user.user_id if isinstance(user, SessionUser) else user
    return uid if isinstance(uid, int) and uid > 0 else None  # phiên "Vào thử" (user_id <= 0) không có dòng trong users nên không có khóa ngoại


def log(level: str, service: str, message: str, user: Union[SessionUser, int, None] = None) -> None:
    """Thêm một dòng nhật ký. Không bao giờ ném lỗi."""
    try:
        if level not in LEVELS:
            raise ValueError(f"Mức nhật ký không hợp lệ: {level}")
        with get_session() as db:
            db.add(SystemLog(level=level, service=clean(service, 50), message=clean(message), user_id=_user_id(user)))
            db.commit()
    except Exception:
        logger.exception("Không ghi được nhật ký hệ thống: %s", clean(message, 120))
