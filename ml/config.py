# Hằng số dùng chung cho tiền xử lý, mô hình và nhãn cảm xúc (báo cáo Mục 2.5, 3.1, 4.1).
# Giá trị đối chiếu với ser_project/configs/config.py; không copy logic huấn luyện.
from typing import Dict, List

SAMPLE_RATE: int = 16000
DURATION: float = 3.0
NUM_SAMPLES: int = 48000  # SAMPLE_RATE * DURATION
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

BACKBONE_NAME: str = "ntu-spml/distilhubert"
LORA_R: int = 8
LORA_ALPHA: int = 16
LORA_DROPOUT: float = 0.1
LORA_TARGET_MODULES: List[str] = ["q_proj", "v_proj"]

CLASSIFIER_HIDDEN_DIM: int = 256
CLASSIFIER_DROPOUT: float = 0.3

NUM_FRAMES: int = 149  # số khung DistilHuBERT cho 3 s (mỗi khung ~20 ms)
CHECKPOINT_NAME: str = "best_distilhubert_lora.pt"
