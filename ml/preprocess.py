# UC03/UC07: tiền xử lý âm thanh (16 kHz mono, cắt lặng top_db=25, chuẩn hóa [-1,1], cố định 48.000 mẫu).
# Port nguyên từ ser_project/src/preprocess.py (báo cáo Mục 3.1.1–3.1.4): phải giống hệt lúc huấn luyện, nếu không số đo sẽ lệch.
from __future__ import annotations

from typing import Tuple

import librosa
import numpy as np

from ml.config import NUM_SAMPLES, SAMPLE_RATE, TOP_DB_TRIM


def load_and_preprocess_audio(path: str) -> np.ndarray:
    """Nạp, đưa về 16 kHz mono, cắt lặng đầu/cuối (top_db=25), chuẩn hóa theo biên độ đỉnh. Độ dài thay đổi (chưa cố định)."""
    y, _ = librosa.load(path, sr=SAMPLE_RATE, mono=True)
    trimmed, _ = librosa.effects.trim(y, top_db=TOP_DB_TRIM)
    if len(trimmed) == 0:  # tệp toàn khoảng lặng: giữ nguyên thay vì trả mảng rỗng
        trimmed = y
    peak = np.max(np.abs(trimmed)) if len(trimmed) else 0.0
    return trimmed / peak if peak > 0 else trimmed


def pad_or_truncate_waveform(waveform: np.ndarray, num_samples: int = NUM_SAMPLES) -> np.ndarray:
    """Đệm số 0 (cuối) hoặc cắt về đúng num_samples mẫu."""
    if len(waveform) < num_samples:
        return np.pad(waveform, (0, num_samples - len(waveform)), mode="constant")
    return waveform[:num_samples]


def preprocess_for_model(path: str) -> Tuple[np.ndarray, float]:
    """(waveform float32 [48000], thời lượng giọng nói thật tính bằng giây, tối đa 3,0)."""
    cleaned = load_and_preprocess_audio(path)
    real_duration = min(len(cleaned) / SAMPLE_RATE, NUM_SAMPLES / SAMPLE_RATE)
    return pad_or_truncate_waveform(cleaned).astype(np.float32), float(real_duration)


def extract_212_features(y: np.ndarray, sr: int = SAMPLE_RATE) -> np.ndarray:
    """212 đặc trưng cho baseline cổ điển: MFCC(40) mean+std, Mel(128) mean, F0 mean/std, RMS mean/std."""
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
    f0 = librosa.yin(y, fmin=65, fmax=2093, sr=sr)
    f0 = f0[~np.isnan(f0)]
    pitch = np.array([np.mean(f0), np.std(f0)]) if len(f0) > 0 else np.array([0.0, 0.0])
    rms = librosa.feature.rms(y=y)
    energy = np.array([np.mean(rms), np.std(rms)])
    features = np.concatenate([np.mean(mfcc, axis=1), np.std(mfcc, axis=1), np.mean(mel, axis=1), pitch, energy])
    return features.astype(np.float32)


def features_212_for_file(path: str) -> np.ndarray:
    """212 đặc trưng của một tệp âm thanh đúng như lúc huấn luyện baseline: tính trên đoạn đã cắt lặng và chuẩn hóa, độ dài thật (không đệm / cắt 3 giây)."""
    return extract_212_features(load_and_preprocess_audio(path))
