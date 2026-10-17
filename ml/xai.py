# XAI (UC04, đề cương tuần 9): Attention Heatmap trên dạng sóng + Attention trên Mel-spectrogram.
# Captum (tùy chọn theo đề cương) chỉ ghi chú, chưa thêm vào requirements.
from __future__ import annotations

from typing import List, Tuple

import numpy as np


def _cell_means(attn_weights: np.ndarray, num_cells: int) -> np.ndarray:
    attn = np.asarray(attn_weights, dtype=np.float64).reshape(-1)
    edges = np.linspace(0, len(attn), num_cells + 1).astype(int)
    return np.array([attn[lo:max(hi, lo + 1)].mean() for lo, hi in zip(edges[:-1], edges[1:])])


def attention_to_levels(attn_weights: np.ndarray, num_levels: int = 5, num_cells: int = 30) -> List[int]:
    """Gom 149 trọng số attention thành num_cells ô thời gian rồi lượng tử hóa thành num_levels mức rời rạc (0..num_levels-1).
    Chuẩn hóa theo ô lớn nhất của chính mẫu này nên mức 0 = ít chú ý nhất, mức cao nhất = chú ý nhiều nhất (không nội suy)."""
    cells = _cell_means(attn_weights, num_cells)
    top = cells.max()
    if top <= 0:
        return [0] * num_cells
    return [min(int(v / top * num_levels), num_levels - 1) for v in cells]


def peak_range(levels: List[int], total: float = 3.0) -> Tuple[float, float]:
    """Khoảng thời gian (giây) liền kề quanh ô chú ý cao nhất, gồm các ô có mức >= mức cao nhất - 1."""
    if not levels:
        return 0.0, total
    peak = max(range(len(levels)), key=lambda i: levels[i])
    bar = max(levels[peak] - 1, 0)
    lo = hi = peak
    while lo > 0 and levels[lo - 1] >= bar:
        lo -= 1
    while hi < len(levels) - 1 and levels[hi + 1] >= bar:
        hi += 1
    cell = total / len(levels)
    return round(lo * cell, 2), round((hi + 1) * cell, 2)


def waveform_envelope(waveform: np.ndarray, num_bars: int = 60) -> List[float]:
    """Biên độ trung bình tuyệt đối theo num_bars đoạn, chuẩn hóa về [0,1], để vẽ dạng sóng."""
    wave = np.abs(np.asarray(waveform, dtype=np.float64).reshape(-1))
    edges = np.linspace(0, len(wave), num_bars + 1).astype(int)
    bars = np.array([wave[lo:max(hi, lo + 1)].mean() for lo, hi in zip(edges[:-1], edges[1:])])
    top = bars.max()
    return (bars / top).tolist() if top > 0 else [0.0] * num_bars


def render_waveform_heatmap(waveform: np.ndarray, attn_weights: np.ndarray, real_duration: float, output_path: str) -> str:
    raise NotImplementedError(
        "TODO UC04 (báo cáo Hình 5.1): vẽ sóng âm + heatmap ô rời rạc 5 mức xanh (#E8EDFC..#4361D8) + vạch nét đứt kết thúc giọng nói thực tế, lưu PNG"
    )


def render_attention_on_mel(waveform: np.ndarray, attn_weights: np.ndarray, output_path: str) -> str:
    raise NotImplementedError(
        "TODO (đề cương tuần 9, mục XAI 'trên spectrogram'; báo cáo chưa làm, xem Mục 5.2): phủ attention lên Mel-spectrogram, lưu PNG vào storage/mel"
    )
