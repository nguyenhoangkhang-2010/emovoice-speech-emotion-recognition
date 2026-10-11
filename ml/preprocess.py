# UC03/UC07: tiền xử lý âm thanh (16 kHz mono, cắt lặng top_db=25, chuẩn hóa [-1,1], cố định 48.000 mẫu).
# TODO: port từ ser_project/src/preprocess.py (báo cáo Mục 3.1.1–3.1.4); chưa copy logic.
from __future__ import annotations

import numpy as np


def load_and_preprocess_audio(path: str) -> np.ndarray:
    raise NotImplementedError(
        "TODO port từ ser_project/src/preprocess.py (báo cáo Mục 3.1.1–3.1.3): load, resample 16 kHz mono, trim top_db=25, chuẩn hóa biên độ"
    )


def pad_or_truncate_waveform(waveform: np.ndarray, num_samples: int = 48000) -> np.ndarray:
    raise NotImplementedError(
        "TODO port từ ser_project/src/preprocess.py (báo cáo Mục 3.1.4): pad số 0 hoặc cắt về NUM_SAMPLES=48.000"
    )
