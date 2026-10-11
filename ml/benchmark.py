# So sánh trước/sau cải tiến (đề cương tuần 8): số tham số, kích thước checkpoint (MiB), độ trễ ms/mẫu — CÙNG quy trình cho mọi mô hình.
# Báo cáo Bảng 5.4 nêu rõ độ trễ hiện chưa đo đồng nhất (Baseline không warm-up/synchronize); module này khắc phục điểm đó.
from __future__ import annotations

from typing import Callable, Dict


def count_parameters(model) -> Dict[str, int]:
    raise NotImplementedError("TODO: trả {'total': ..., 'trainable': ...}; DistilHuBERT + LoRA mong đợi 23.741.321 / 249.353 (1,05%)")


def checkpoint_size_mib(path: str) -> float:
    raise NotImplementedError("TODO: kích thước tệp checkpoint theo MiB (best_distilhubert_lora.pt ≈ 90,6 MiB, báo cáo Bảng 4.9)")


def measure_latency_ms(predict_fn: Callable, sample, warmup: int = 2, repeats: int = 180) -> float:
    raise NotImplementedError("TODO: warm-up + torch.cuda.synchronize() trước/sau khi đo, trả ms/mẫu; dùng cho HuBERT-base, wav2vec 2.0 gốc, DistilHuBERT + LoRA và các baseline")


def run_benchmark(output_dir: str = "assets/metrics") -> Dict[str, Dict[str, float]]:
    raise NotImplementedError("TODO: chạy cho mọi mô hình (HuBERT-base/wav2vec 2.0 gốc chưa đo) và ghi vào model_metrics.json")
