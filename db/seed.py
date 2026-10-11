# Dữ liệu ban đầu: 8 cảm xúc, bảng models (số liệu báo cáo Bảng 5.1–5.4, 4.7), 1 admin mặc định từ .env.
# Hằng số bên dưới là dữ liệu mẫu cứng; seed() CHƯA cài đặt. inference_time tính theo ms/mẫu (báo cáo Bảng 5.4).
from ml.config import EMOTION_NAMES, EMOTION_NAMES_VI

SEED_EMOTIONS = [
    {"emotion_id": i, "name": name, "name_vi": name_vi}
    for i, (name, name_vi) in enumerate(zip(EMOTION_NAMES, EMOTION_NAMES_VI))
]

SEED_MODELS = [
    {"name": "Random Forest", "model_type": "Cổ điển", "accuracy": 52.22, "f1_score": 48.11, "size_mb": None, "inference_time": 0.09, "is_active": False},
    {"name": "XGBoost", "model_type": "Cổ điển", "accuracy": 48.89, "f1_score": 47.07, "size_mb": None, "inference_time": 0.04, "is_active": False},
    # 34.120 tham số, checkpoint 0,14 MiB (Bảng 5.3). inference_time 4,16 ms theo Bảng 5.4 (Bảng 4.6 ghi 1,19 ms: cần thống nhất).
    {"name": "1D-CNN", "model_type": "Mạng sâu", "accuracy": 36.11, "f1_score": 29.47, "size_mb": 0.14, "inference_time": 4.16, "is_active": False},
    # 143.944 tham số. TODO: đối chiếu F1 32,80 (Bảng 5.1) với 33,37 (Mục 4.2) trước khi điền; báo cáo cũng nêu lần chạy chính 38,33 / 37,05.
    {"name": "Bi-LSTM", "model_type": "Mạng sâu", "accuracy": 36.67, "f1_score": None, "size_mb": None, "inference_time": 0.02, "is_active": False},
    # 249.353 / 23.741.321 tham số huấn luyện (1,05%), checkpoint tốt nhất 90,6 MiB.
    {"name": "DistilHuBERT + LoRA", "model_type": "Transformer", "accuracy": 73.33, "f1_score": 71.21, "size_mb": 90.6, "inference_time": 7.60, "is_active": True},
]


def seed() -> None:
    raise NotImplementedError(
        "TODO UC01/UC06 (báo cáo Mục 2.4): idempotent — tạo bảng, nạp SEED_EMOTIONS, SEED_MODELS và admin mặc định "
        "(mật khẩu băm từ settings.admin_password qua core.security.hash_password)"
    )
