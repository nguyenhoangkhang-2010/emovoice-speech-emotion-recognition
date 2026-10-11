# UC03/UC07 (báo cáo Bảng 2.5, 2.9): điều phối tiền xử lý và trích đặc trưng lưu vào audio_features.
import numpy as np


def preprocess_audio(file_path: str) -> np.ndarray:
    raise NotImplementedError("TODO UC03/UC07: gọi ml.preprocess.load_and_preprocess_audio rồi pad_or_truncate_waveform -> 48.000 mẫu")


def save_audio_features(audio_id: int, waveform: np.ndarray) -> None:
    raise NotImplementedError("TODO: tính trimmed_duration, mfcc_mean, f0_mean, voiced_ratio, rms_mean, ảnh mel (storage/mel); ghi audio_features 1-1")


def compute_input_diagnostics(file_path: str) -> dict:
    raise NotImplementedError("TODO (khung Stitch 'Tham số âm phổ ban đầu'): SNR, F0, ZCR để hiện ở trang Phân tích mới")
