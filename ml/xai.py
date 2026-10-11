# XAI (UC04, đề cương tuần 9): Attention Heatmap trên dạng sóng + Attention trên Mel-spectrogram.
# Captum (tùy chọn theo đề cương) chỉ ghi chú, chưa thêm vào requirements.
from __future__ import annotations

from typing import List

import numpy as np


def attention_to_levels(attn_weights: np.ndarray, num_levels: int = 5) -> List[int]:
    raise NotImplementedError("TODO UC04 (báo cáo Mục 5.2): lượng tử hóa 149 trọng số thành num_levels=5 mức rời rạc (0..4), không nội suy gradient")


def render_waveform_heatmap(waveform: np.ndarray, attn_weights: np.ndarray, real_duration: float, output_path: str) -> str:
    raise NotImplementedError(
        "TODO UC04 (báo cáo Hình 5.1): vẽ sóng âm + heatmap ô rời rạc 5 mức xanh (#E8EDFC..#4361D8) + vạch nét đứt kết thúc giọng nói thực tế, lưu PNG"
    )


def render_attention_on_mel(waveform: np.ndarray, attn_weights: np.ndarray, output_path: str) -> str:
    raise NotImplementedError(
        "TODO (đề cương tuần 9, mục XAI 'trên spectrogram'; báo cáo chưa làm, xem Mục 5.2): phủ attention lên Mel-spectrogram, lưu PNG vào storage/mel"
    )
