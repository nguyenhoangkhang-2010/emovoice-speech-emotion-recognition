# XAI trên Mel-spectrogram (UC04, đề cương tuần 9): tính Mel, vẽ vùng chú ý, lưu ảnh. Không nạp mô hình.
import numpy as np
import pytest

from core.config import Settings
from ml import xai
from services import xai_service

PNG = b"\x89PNG\r\n\x1a\n"


def _wave(seconds=3.0):
    t = np.arange(int(seconds * 16000)) / 16000
    return (0.4 * np.sin(2 * np.pi * 300 * t) * (t < 1.5)).astype(np.float32)  # tiếng "nói" 1,5 s rồi im lặng


def _attention(peak_frame=60):
    attn = np.full(149, 0.001)
    attn[peak_frame : peak_frame + 15] = 0.05
    return attn


def test_mel_spectrogram_has_expected_shape_and_range():
    db = xai.mel_spectrogram_db(_wave())
    assert db.shape == (128, 301)  # 128 dải Mel x ~301 khung (bước 10 ms cho 3 giây)
    assert np.isfinite(db).all() and db.max() == pytest.approx(0.0) and db.min() >= -80.0  # theo dB, mốc 0 dB là điểm sáng nhất


def test_mel_of_pure_silence_is_finite():
    db = xai.mel_spectrogram_db(np.zeros(48000, dtype=np.float32))
    assert np.isfinite(db).all()  # tệp im lặng hoàn toàn không làm hỏng ảnh


def test_render_attention_on_mel_writes_png(tmp_path):
    out = xai.render_attention_on_mel(_wave(), _attention(), str(tmp_path / "mel.png"), 1.5)
    assert out.endswith("mel.png") and (tmp_path / "mel.png").read_bytes()[:8] == PNG


def test_render_handles_flat_or_zero_attention_and_any_real_duration(tmp_path):
    for i, (attn, duration) in enumerate(((np.zeros(149), 3.0), (np.ones(149), 0.4), (_attention(0), 2.9))):
        path = str(tmp_path / f"m{i}.png")
        assert xai.render_attention_on_mel(_wave(), attn, path, duration) == path
        assert (tmp_path / f"m{i}.png").stat().st_size > 5000


def test_build_mel_attention_saves_uuid_png_in_mel_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(Settings, "mel_dir", property(lambda self: tmp_path / "mel"))
    first = xai_service.build_mel_attention(_wave(), _attention(), 1.5)
    second = xai_service.build_mel_attention(_wave(), _attention())
    assert first != second and first.endswith(".png") and (tmp_path / "mel") in __import__("pathlib").Path(first).parents
    assert len(list((tmp_path / "mel").glob("*.png"))) == 2


def test_save_audio_features_stores_mel_path_only_when_given(monkeypatch):
    from contextlib import contextmanager

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    import models  # noqa: F401
    from db.base import Base
    from models.audio_feature import AudioFeature
    from models.audio_file import AudioFile
    from models.user import User
    from services import preprocessing_service

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False)

    @contextmanager
    def fake():
        s = factory()
        try:
            yield s
        finally:
            s.close()

    monkeypatch.setattr(preprocessing_service, "get_session", fake)
    with fake() as s:
        s.add(User(username="a", email="a@x.vn", password="h"))
        s.flush()
        s.add(AudioFile(user_id=1, filename="a.wav", file_path="/a.wav", duration=3.0))
        s.commit()
    preprocessing_service.save_audio_features(1, _wave(), 1.5)
    with fake() as s:
        assert s.get(AudioFeature, 1).mel_image_path is None
    preprocessing_service.save_audio_features(1, _wave(), 1.5, "/mel/a.png")
    preprocessing_service.save_audio_features(1, _wave(), 1.5)  # ghi lại không kèm ảnh thì giữ nguyên đường dẫn đã có
    with fake() as s:
        assert s.get(AudioFeature, 1).mel_image_path == "/mel/a.png"
