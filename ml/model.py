# Kiến trúc DistilHuBERT (đóng băng) + LoRA + Temporal Attention Pooling + head 8 lớp (báo cáo Mục 2.5, 4.3).
# Port nguyên từ ser_project/src/model_transformer.py: tên lớp và tên tham số phải KHỚP để nạp được state_dict của best_distilhubert_lora.pt.
from __future__ import annotations

import torch
from torch import nn

from ml.config import (
    BACKBONE_NAME,
    CLASSIFIER_DROPOUT,
    CLASSIFIER_HIDDEN_DIM,
    LORA_ALPHA,
    LORA_DROPOUT,
    LORA_R,
    LORA_TARGET_MODULES,
    NUM_CLASSES,
)


class TemporalAttentionPooling(nn.Module):
    def __init__(self, hidden_dim: int = 768) -> None:
        super().__init__()
        self.projection = nn.Linear(hidden_dim, 1)

    def forward(self, hidden_states: torch.Tensor):
        """hidden_states [B, T, 768] -> (pooled [B, 768], attn_weights [B, T, 1]); T = 149 khung cho 3 s."""
        attn_weights = torch.softmax(self.projection(hidden_states), dim=1)
        pooled = torch.sum(hidden_states * attn_weights, dim=1)
        return pooled, attn_weights


class DistilHuBERTForSER(nn.Module):
    def __init__(self, num_classes: int = NUM_CLASSES) -> None:
        super().__init__()
        from peft import LoraConfig, get_peft_model
        from transformers import AutoModel

        self.hubert = AutoModel.from_pretrained(BACKBONE_NAME)
        for param in self.hubert.parameters():  # đóng băng toàn bộ trọng số gốc
            param.requires_grad = False
        lora = LoraConfig(r=LORA_R, lora_alpha=LORA_ALPHA, target_modules=LORA_TARGET_MODULES, lora_dropout=LORA_DROPOUT, bias="none")
        self.hubert = get_peft_model(self.hubert, lora)
        self.pooling = TemporalAttentionPooling(hidden_dim=768)
        self.classifier = nn.Sequential(
            nn.Linear(768, CLASSIFIER_HIDDEN_DIM),
            nn.GELU(),
            nn.LayerNorm(CLASSIFIER_HIDDEN_DIM),
            nn.Dropout(CLASSIFIER_DROPOUT),
            nn.Linear(CLASSIFIER_HIDDEN_DIM, num_classes),
        )

    def forward(self, input_values: torch.Tensor):
        """input_values [B, 48000] -> (logits [B, 8], attn_weights [B, 149, 1]) để UC04 vẽ XAI."""
        hidden_states = self.hubert(input_values).last_hidden_state
        pooled, attn_weights = self.pooling(hidden_states)
        return self.classifier(pooled), attn_weights
