# UC04: tạo biểu đồ XAI (heatmap trên dạng sóng, attention trên Mel) và trả đường dẫn tệp ảnh.
import numpy as np


def build_waveform_heatmap(waveform: np.ndarray, attn_weights: np.ndarray, real_duration: float) -> str:
    raise NotImplementedError("TODO UC04: gọi ml.xai.render_waveform_heatmap, lưu storage/heatmaps với tên uuid, trả đường dẫn")


def build_mel_attention(waveform: np.ndarray, attn_weights: np.ndarray) -> str:
    raise NotImplementedError("TODO (đề cương tuần 9, XAI trên spectrogram): gọi ml.xai.render_attention_on_mel, lưu storage/mel")
