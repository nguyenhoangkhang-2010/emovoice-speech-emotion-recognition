# Hằng số dùng chung cho tiền xử lý, mô hình và nhãn cảm xúc.
# Giá trị đối chiếu với ser_project/configs/config.py; không copy logic huấn luyện.
from typing import Dict, List

SAMPLE_RATE: int = 16000
DURATION: float = 3.0
NUM_SAMPLES: int = 48000
TOP_DB_TRIM: int = 25

NUM_CLASSES: int = 8
LABEL_MAP: Dict[str, int] = {
    "neutral": 0,
    "calm": 1,
    "happy": 2,
    "sad": 3,
    "angry": 4,
    "fearful": 5,
    "disgust": 6,
    "surprised": 7,
}
EMOTION_NAMES: List[str] = ["neutral", "calm", "happy", "sad", "angry", "fearful", "disgust", "surprised"]
EMOTION_NAMES_VI: List[str] = [
    "Trung tính",
    "Êm đềm",
    "Vui vẻ",
    "Buồn bã",
    "Tức giận",
    "Sợ hãi",
    "Chán ghét",
    "Ngạc nhiên",
]

# Bộ nhãn của từng tập dữ liệu: mô hình RAVDESS 8 nhãn (mô hình chính) và mô hình CREMA-D 6 nhãn (chỉ để so sánh).
CREMAD6_NAMES: List[str] = ["neutral", "happy", "sad", "angry", "fearful", "disgust"]
CREMAD6_NAMES_VI: List[str] = ["Trung tính", "Vui vẻ", "Buồn bã", "Tức giận", "Sợ hãi", "Chán ghét"]
DEFAULT_LABEL_SET: str = "ravdess8"
LABEL_SETS: Dict[str, Dict[str, List[str]]] = {
    "ravdess8": {"names": EMOTION_NAMES, "names_vi": EMOTION_NAMES_VI},
    "cremad6": {"names": CREMAD6_NAMES, "names_vi": CREMAD6_NAMES_VI},
}

BACKBONE_NAME: str = "ntu-spml/distilhubert"
LORA_R: int = 8
LORA_ALPHA: int = 16
LORA_DROPOUT: float = 0.1
LORA_TARGET_MODULES: List[str] = ["q_proj", "v_proj"]

CLASSIFIER_HIDDEN_DIM: int = 256
CLASSIFIER_DROPOUT: float = 0.3

NUM_FRAMES: int = 149  # số khung DistilHuBERT cho 3 s (mỗi khung ~20 ms)
CHECKPOINT_NAME: str = "best_distilhubert_lora.pt"
