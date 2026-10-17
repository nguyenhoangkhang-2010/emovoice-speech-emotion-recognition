# UC04: tạo biểu đồ XAI (heatmap trên dạng sóng, attention trên Mel) và trả đường dẫn tệp ảnh.
import uuid

import numpy as np

from core.config import settings


def build_waveform_heatmap(waveform: np.ndarray, attn_weights: np.ndarray, real_duration: float) -> str:
    """Vẽ heatmap attention trên dạng sóng, lưu storage/heatmaps/<uuid>.png và trả đường dẫn."""
    from ml import xai

    settings.heatmap_dir.mkdir(parents=True, exist_ok=True)
    return xai.render_waveform_heatmap(waveform, attn_weights, real_duration, str(settings.heatmap_dir / f"{uuid.uuid4().hex}.png"))


def build_mel_attention(waveform: np.ndarray, attn_weights: np.ndarray) -> str:
    raise NotImplementedError("TODO (đề cương tuần 9, XAI trên spectrogram): gọi ml.xai.render_attention_on_mel, lưu storage/mel")
