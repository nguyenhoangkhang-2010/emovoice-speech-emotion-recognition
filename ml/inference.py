# Nạp checkpoint best_distilhubert_lora.pt (state_dict) và dự đoán trên waveform 48.000 mẫu.
from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional, Tuple, Union

import numpy as np
import torch

from ml.config import NUM_CLASSES, NUM_SAMPLES
from ml.model import DistilHuBERTForSER

_cache = {"model": None, "path": None, "device": None}
_aux_models: dict = {}  # mô hình chỉ để so sánh (ví dụ CREMA-D 6 nhãn), nạp một lần theo đường dẫn, không thay mô hình chính
_lock = threading.Lock()  # Gradio chạy nhiều yêu cầu song song: chỉ nạp mô hình một lần


def pick_device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def build_model(checkpoint_path: Union[str, Path], device: Optional[torch.device] = None, num_classes: int = NUM_CLASSES) -> DistilHuBERTForSER:
    """Dựng DistilHuBERT + LoRA, nạp state_dict từ tệp, chuyển eval(). Không cache (dùng khi đăng ký / đánh giá)."""
    device = device or pick_device()
    state = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    model = DistilHuBERTForSER(num_classes)
    if isinstance(state.get("state"), dict):
        # tệp huấn luyện lại (CREMA-D) chỉ lưu LoRA + pooling + head; backbone đóng băng lấy từ ntu-spml/distilhubert
        result = model.load_state_dict(state["state"], strict=False)
        trainable = {name for name, param in model.named_parameters() if param.requires_grad}
        bad = [key for key in result.missing_keys if key in trainable] + list(result.unexpected_keys)
        if bad:
            raise RuntimeError(f"Checkpoint không khớp mô hình, khóa lệch: {bad[:5]}")
    else:
        model.load_state_dict(state)  # strict: khóa nào lệch tên sẽ báo lỗi ngay, không nạp thiếu âm thầm
    return model.to(device).eval()


def load_model(checkpoint_path: Optional[str] = None) -> DistilHuBERTForSER:
    """Nạp một lần rồi dùng lại (yêu cầu phi chức năng: suy luận < 1,5 s). Đổi đường dẫn thì nạp lại."""
    from core.config import settings

    path = str(Path(checkpoint_path) if checkpoint_path else settings.checkpoint_path)
    with _lock:
        if _cache["model"] is None or _cache["path"] != path:
            device = pick_device()
            _cache.update(model=build_model(path, device), path=path, device=device)
        return _cache["model"]


def predict_aux(waveform: np.ndarray, checkpoint_path: str, num_classes: int) -> np.ndarray:
    """Xác suất [num_classes] của một mô hình PHỤ (chỉ để so sánh, ví dụ CREMA-D 6 nhãn) trên waveform 48.000 mẫu. Không đụng tới mô hình chính."""
    wave = np.asarray(waveform, dtype=np.float32).reshape(-1)
    if wave.shape[0] != NUM_SAMPLES:
        raise ValueError(f"Cần đúng {NUM_SAMPLES} mẫu (3 s ở 16 kHz), nhận {wave.shape[0]}.")
    path = str(checkpoint_path)
    with _lock:
        if path not in _aux_models:
            device = pick_device()
            _aux_models[path] = (build_model(path, device, num_classes), device)
        model, device = _aux_models[path]
    with torch.no_grad():
        logits, _ = model(torch.from_numpy(wave).unsqueeze(0).to(device))
    return torch.softmax(logits[0].float().cpu(), dim=0).numpy()


def loaded_info() -> dict:
    """Mô hình đang nằm trong bộ nhớ (cho trang trạng thái hệ thống): {'loaded', 'path', 'device'}."""
    return {"loaded": _cache["model"] is not None, "path": _cache["path"], "device": str(_cache["device"]) if _cache["device"] else None}


def predict(waveform: np.ndarray, checkpoint_path: Optional[str] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """waveform [48000] float32 -> (logits [8], probs [8], attn_weights [149])."""
    wave = np.asarray(waveform, dtype=np.float32).reshape(-1)
    if wave.shape[0] != NUM_SAMPLES:
        raise ValueError(f"Cần đúng {NUM_SAMPLES} mẫu (3 s ở 16 kHz), nhận {wave.shape[0]}.")
    model = load_model(checkpoint_path)
    with torch.no_grad():
        logits, attn = model(torch.from_numpy(wave).unsqueeze(0).to(_cache["device"]))
    logits = logits[0].cpu().numpy()
    probs = torch.softmax(torch.from_numpy(logits), dim=0).numpy()
    return logits, probs, attn[0, :, 0].cpu().numpy()
