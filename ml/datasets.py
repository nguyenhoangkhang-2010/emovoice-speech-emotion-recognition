# Label map các bộ dữ liệu SER dùng cho huấn luyện và kiểm thử chéo (báo cáo Mục 1.4, 3.3; đề cương mục Thu thập dữ liệu).
# TODO: viết loader TESS/CREMA-D (kiểm thử chéo, chưa làm) và ghi chú nguồn tiếng Việt (VLSP hoặc tự thu âm, mở rộng, chưa làm).
from typing import Dict

# RAVDESS (đã dùng): trường thứ 3 của tên tệp -> nhãn 8 lớp (báo cáo Mục 1.4.1)
RAVDESS_EMOTION_CODE: Dict[str, str] = {
    "01": "neutral",
    "02": "calm",
    "03": "happy",
    "04": "sad",
    "05": "angry",
    "06": "fearful",
    "07": "disgust",
    "08": "surprised",
}

# TESS (kiểm thử chéo, chưa làm): tên thư mục/hậu tố -> nhãn. Không có "calm" nên chỉ đánh giá được 7/8 lớp.
TESS_EMOTION_LABEL: Dict[str, str] = {
    "neutral": "neutral",
    "happy": "happy",
    "sad": "sad",
    "angry": "angry",
    "fear": "fearful",
    "disgust": "disgust",
    "ps": "surprised",  # "pleasant surprise"
}

# CREMA-D (kiểm thử chéo, chưa làm): mã trong tên tệp -> nhãn. Chỉ có 6 nhãn (không có calm, surprised).
CREMA_D_EMOTION_CODE: Dict[str, str] = {
    "NEU": "neutral",
    "HAP": "happy",
    "SAD": "sad",
    "ANG": "angry",
    "FEA": "fearful",
    "DIS": "disgust",
}

# Mở rộng tiếng Việt (chưa làm): VLSP hoặc tự thu âm nhỏ — chưa có label map vì chưa chọn nguồn dữ liệu.


def load_ravdess_metadata(root_dir: str):
    raise NotImplementedError("TODO port từ ser_project (báo cáo Mục 3.3.1): duyệt RAVDESS, tách Actor 1–18 / 19–21 / 22–24 (train/val/test độc lập người nói)")


def load_tess_metadata(root_dir: str):
    raise NotImplementedError("TODO kiểm thử chéo TESS (đề cương tuần 7–8; báo cáo Mục 1.4.2): trả danh sách (đường dẫn, nhãn 8 lớp)")


def load_crema_d_metadata(root_dir: str):
    raise NotImplementedError("TODO kiểm thử chéo CREMA-D (đề cương tuần 7–8; báo cáo Mục 1.4.2): trả danh sách (đường dẫn, nhãn, chỉ 6 lớp)")
