# UC04: tạo biểu đồ XAI (heatmap trên dạng sóng, attention trên Mel) và trả đường dẫn tệp ảnh.
import uuid

import numpy as np

from core.config import settings


def build_waveform_heatmap(waveform: np.ndarray, attn_weights: np.ndarray, real_duration: float) -> str:
    """Vẽ heatmap attention trên dạng sóng, lưu storage/heatmaps/<uuid>.png và trả đường dẫn."""
    from ml import xai

    settings.heatmap_dir.mkdir(parents=True, exist_ok=True)
    return xai.render_waveform_heatmap(waveform, attn_weights, real_duration, str(settings.heatmap_dir / f"{uuid.uuid4().hex}.png"))


def build_mel_attention(waveform: np.ndarray, attn_weights: np.ndarray, real_duration: float = 3.0) -> str:
    """Vẽ Mel-spectrogram có phủ vùng chú ý, lưu storage/mel/<uuid>.png và trả đường dẫn."""
    from ml import xai

    settings.mel_dir.mkdir(parents=True, exist_ok=True)
    return xai.render_attention_on_mel(waveform, attn_weights, str(settings.mel_dir / f"{uuid.uuid4().hex}.png"), real_duration)
