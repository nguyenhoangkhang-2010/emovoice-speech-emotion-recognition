# UC03/UC07 tiền xử lý (báo cáo Mục 3.1): 16 kHz mono, cắt lặng top_db=25, chuẩn hóa [-1,1], cố định 48.000 mẫu.
import numpy as np
import pytest

sf = pytest.importorskip("soundfile")

from ml import preprocess  # noqa: E402
from ml.config import NUM_SAMPLES, SAMPLE_RATE  # noqa: E402


def _write(path, signal, rate=SAMPLE_RATE):
    sf.write(str(path), signal.astype(np.float32), rate)
    return str(path)


def _tone(seconds, rate=SAMPLE_RATE, amp=0.3, freq=220.0):
    t = np.arange(int(seconds * rate)) / rate
    return amp * np.sin(2 * np.pi * freq * t)


def test_output_is_exactly_48000_samples(tmp_path):
    for seconds in (1.0, 3.0, 5.0):
        wave, duration = preprocess.preprocess_for_model(_write(tmp_path / f"{seconds}.wav", _tone(seconds)))
        assert wave.shape == (NUM_SAMPLES,) and wave.dtype == np.float32
        assert 0 < duration <= 3.0


def test_real_duration_reflects_trimmed_speech(tmp_path):
    padded = np.concatenate([np.zeros(SAMPLE_RATE), _tone(1.0), np.zeros(SAMPLE_RATE)])
    _, duration = preprocess.preprocess_for_model(_write(tmp_path / "padded.wav", padded))
    assert 0.9 <= duration <= 1.2  # khoảng lặng đầu/cuối đã bị cắt


def test_amplitude_normalized_and_silence_safe(tmp_path):
    wave, _ = preprocess.preprocess_for_model(_write(tmp_path / "quiet.wav", _tone(1.0, amp=0.05)))
    assert np.max(np.abs(wave)) == pytest.approx(1.0, abs=1e-5)  # chuẩn hóa theo biên độ đỉnh
    silent, duration = preprocess.preprocess_for_model(_write(tmp_path / "silent.wav", np.zeros(SAMPLE_RATE)))
    assert silent.shape == (NUM_SAMPLES,) and not np.isnan(silent).any() and duration > 0


def test_resamples_and_mixes_to_mono(tmp_path):
    stereo = np.stack([_tone(1.0, rate=44100), _tone(1.0, rate=44100, freq=330)], axis=1)
    path = tmp_path / "stereo.wav"
    sf.write(str(path), stereo.astype(np.float32), 44100)
    assert len(preprocess.load_and_preprocess_audio(str(path))) <= SAMPLE_RATE + 200  # ~1 s ở 16 kHz


def test_features_212_shape(tmp_path):
    features = preprocess.extract_212_features(_tone(2.0))
    assert features.shape == (212,) and features.dtype == np.float32
