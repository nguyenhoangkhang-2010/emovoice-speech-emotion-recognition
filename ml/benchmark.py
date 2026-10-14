# Số tham số, kích thước checkpoint (MiB), độ trễ ms/mẫu — đo THẬT trên mô hình đã nạp (đề cương tuần 8).
# Độ trễ phụ thuộc thiết bị (cpu/cuda) nên luôn ghi kèm thiết bị; báo cáo Bảng 5.4 nêu độ trễ chưa đo đồng nhất giữa các mô hình.
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Dict, Union


def count_parameters(model) -> Dict[str, int]:
    """{'total', 'trainable'}; DistilHuBERT + LoRA của báo cáo: 23.741.321 / 249.353 (1,05%)."""
    params = list(model.parameters())
    return {"total": sum(p.numel() for p in params), "trainable": sum(p.numel() for p in params if p.requires_grad)}


def checkpoint_size_mib(path: Union[str, Path]) -> float:
    return round(Path(path).stat().st_size / (1024 * 1024), 2)


def measure_latency_ms(predict_fn: Callable, sample, warmup: int = 3, repeats: int = 30, sync: Callable = lambda: None) -> float:
    """Trung bình ms cho một lần predict_fn(sample) (batch 1) sau khi khởi động; sync() dùng cho cuda (torch.cuda.synchronize)."""
    for _ in range(warmup):
        predict_fn(sample)
    sync()
    start = time.perf_counter()
    for _ in range(repeats):
        predict_fn(sample)
    sync()
    return round((time.perf_counter() - start) / repeats * 1000, 2)
