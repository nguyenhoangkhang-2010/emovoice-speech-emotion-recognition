# UC03/UC07 (báo cáo Bảng 2.5, 2.9): điều phối tiền xử lý và trích đặc trưng lưu vào audio_features.
from typing import Optional, Tuple

import numpy as np

from db.session import get_session


def preprocess_audio(file_path: str) -> np.ndarray:
    """Tệp âm thanh -> waveform float32 đúng 48.000 mẫu (16 kHz mono, cắt lặng, chuẩn hóa biên độ, đệm/cắt 3 giây)."""
    return preprocess_with_duration(file_path)[0]


def preprocess_with_duration(file_path: str) -> Tuple[np.ndarray, float]:
    """Như preprocess_audio nhưng kèm thời lượng giọng nói thật (giây, tối đa 3,0) để vẽ vạch kết thúc trên heatmap."""
    from ml.preprocess import preprocess_for_model

    return preprocess_for_model(file_path)


def save_audio_features(audio_id: int, waveform: np.ndarray, real_duration: float, mel_image_path: Optional[str] = None) -> None:
    """Đặc trưng tóm tắt của đoạn giọng nói thật (đã cắt lặng) -> audio_features (1-1 với audio_files, ghi đè nếu đã có).
    mfcc_mean là trung bình 40 hệ số MFCC, voiced_ratio là tỉ lệ khung có năng lượng đáng kể (>10% đỉnh); mel_image_path là ảnh Mel + attention (nếu có)."""
    import librosa

    from ml.config import SAMPLE_RATE
    from models.audio_feature import AudioFeature

    speech = np.asarray(waveform, dtype=np.float32)[: max(int(real_duration * SAMPLE_RATE), 2048)]
    rms = librosa.feature.rms(y=speech)[0]
    f0 = librosa.yin(speech, fmin=65, fmax=2093, sr=SAMPLE_RATE)
    f0 = f0[(~np.isnan(f0)) & (f0 > 65) & (f0 < 2093)]
    values = dict(
        trimmed_duration=float(real_duration),
        mfcc_mean=float(np.mean(librosa.feature.mfcc(y=speech, sr=SAMPLE_RATE, n_mfcc=40))),
        f0_mean=float(np.mean(f0)) if len(f0) else None,
        voiced_ratio=float(np.mean(rms > 0.1 * rms.max())) if rms.max() > 0 else 0.0,
        rms_mean=float(np.mean(rms)),
    )
    if mel_image_path:
        values["mel_image_path"] = mel_image_path
    with get_session() as db:
        row = db.get(AudioFeature, audio_id)
        if row is None:
            db.add(AudioFeature(audio_id=audio_id, **values))
        else:
            for key, value in values.items():
                setattr(row, key, value)
        db.commit()


def compute_input_diagnostics(file_path: str) -> dict:
    """Ước lượng từ chính tệp: {'snr_db', 'f0_hz', 'zcr'} (giá trị None nếu không tính được).
    SNR ước lượng bằng tỉ lệ RMS khung phân vị 90 so với phân vị 10 (không có bản ghi nhiễu riêng để so)."""
    import librosa

    from ml.config import SAMPLE_RATE

    y, _ = librosa.load(file_path, sr=SAMPLE_RATE, mono=True)
    if len(y) < 2048:
        return {"snr_db": None, "f0_hz": None, "zcr": None}
    rms = librosa.feature.rms(y=y)[0]
    rms = rms[rms > 1e-5]  # bỏ đoạn im lặng tuyệt đối (đệm số 0) kẻo mẫu số bằng 0
    if len(rms) < 2:
        return {"snr_db": None, "f0_hz": None, "zcr": None}
    high, low = np.percentile(rms, 90), np.percentile(rms, 10)
    snr = float(20 * np.log10(high / low)) if low > 1e-8 and high > 0 else None
    f0 = librosa.yin(y, fmin=65, fmax=2093, sr=SAMPLE_RATE)
    voiced = f0[(~np.isnan(f0)) & (f0 > 65) & (f0 < 2093)]
    return {
        "snr_db": snr,
        "f0_hz": float(np.median(voiced)) if len(voiced) else None,
        "zcr": float(np.mean(librosa.feature.zero_crossing_rate(y)[0])),
    }
