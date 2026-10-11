# Kiến trúc DistilHuBERT (đóng băng) + LoRA + Temporal Attention Pooling + head 8 lớp (báo cáo Mục 2.5, 4.3).
# TODO: port từ ser_project/src/model_transformer.py; forward trả (logits, attn_weights).
from __future__ import annotations

from torch import nn


class TemporalAttentionPooling(nn.Module):
    def __init__(self, hidden_dim: int = 768) -> None:
        raise NotImplementedError(
            "TODO port từ ser_project/src/model_transformer.py (báo cáo Mục 2.5.2): Linear 768->1, softmax theo thời gian"
        )

    def forward(self, hidden_states):
        raise NotImplementedError("TODO (báo cáo Mục 5.2.1): trả (pooled, attn_weights) với attn_weights có 149 khung / 3 s")


class DistilHuBERTForSER(nn.Module):
    def __init__(self) -> None:
        raise NotImplementedError(
            "TODO port (báo cáo Mục 2.5.1, 2.5.3): backbone ntu-spml/distilhubert đóng băng + LoRA q_proj/v_proj + pooling + head 768->256->GELU->LayerNorm->Dropout(0.3)->8"
        )

    def forward(self, input_values):
        raise NotImplementedError("TODO trả (logits, attn_weights) để UC04 vẽ XAI")
