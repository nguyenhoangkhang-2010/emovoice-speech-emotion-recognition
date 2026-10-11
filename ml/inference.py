# UC04: nạp checkpoint best_distilhubert_lora.pt (state_dict) và dự đoán trên waveform 48.000 mẫu.
# TODO: dựa trên ser_project/train_transformer.py (cách nạp state_dict, báo cáo Mục 4.3.3) và ml/model.py.
from __future__ import annotations

from typing import Optional, Tuple

import numpy as np


def load_model(checkpoint_path: Optional[str] = None):
    raise NotImplementedError("TODO UC04: nạp state_dict vào DistilHuBERTForSER, eval(), chọn cpu/cuda, cache một lần (yêu cầu < 1,5 s)")


def predict(waveform: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    raise NotImplementedError("TODO UC04: trả (logits [8], probs [8], attn_weights [149]) bằng torch.no_grad()")
