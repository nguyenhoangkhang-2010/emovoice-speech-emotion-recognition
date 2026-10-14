# Dữ liệu ban đầu tối thiểu: 8 nhãn cảm xúc (lấy từ ml.config) và 1 admin mặc định từ .env.
# KHÔNG nạp bảng models: các mô hình và số đo của chúng được ghi vào sau khi đăng ký / đánh giá mô hình thật, không chép tay vào mã.
from ml.config import EMOTION_NAMES, EMOTION_NAMES_VI

SEED_EMOTIONS = [
    {"emotion_id": i, "name": name, "name_vi": name_vi}
    for i, (name, name_vi) in enumerate(zip(EMOTION_NAMES, EMOTION_NAMES_VI))
]


def seed() -> None:
    """Nạp dữ liệu ban đầu, chạy lại bao nhiêu lần cũng không tạo trùng: 8 cảm xúc và 1 admin từ .env.

    Chạy sau `alembic upgrade head` (bảng phải có sẵn): python -m db.seed
    """
    from sqlalchemy import select

    from core.config import settings
    from core.security import hash_password
    from db.session import get_session
    from models.emotion import Emotion
    from models.user import ROLE_ADMIN, User

    with get_session() as db:
        have_emotions = set(db.scalars(select(Emotion.emotion_id)))
        db.add_all(Emotion(**row) for row in SEED_EMOTIONS if row["emotion_id"] not in have_emotions)

        if db.scalar(select(User.user_id).where(User.username == settings.admin_username)) is None:
            db.add(
                User(
                    username=settings.admin_username,
                    email=settings.admin_email.lower(),
                    password=hash_password(settings.admin_password),
                    role=ROLE_ADMIN,
                    full_name="Quản trị viên",
                )
            )
        db.commit()


if __name__ == "__main__":
    seed()
    print("Đã nạp dữ liệu ban đầu.")
