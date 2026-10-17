# UC02 + UC04: kiểm tra tệp, lưu tệp/đặc trưng/kết quả vào CSDL, ảnh XAI và luồng của trang Phân tích. SQLite trong bộ nhớ, không nạp mô hình PyTorch.
from contextlib import contextmanager

import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401  (đăng ký bảng vào Base.metadata)
from core.config import Settings
from core.session import PermissionDenied, SessionUser
from db.base import Base
from db import session as db_session
from ml import xai
from ml.config import EMOTION_NAMES, EMOTION_NAMES_VI
from models.audio_feature import AudioFeature
from models.audio_file import AudioFile
from models.emotion import Emotion
from models.ml_model import MLModel
from models.prediction import Prediction
from models.prediction_score import PredictionScore
from models.user import User
from services import audio_service, inference_service, preprocessing_service

sf = pytest.importorskip("soundfile")


@pytest.fixture()
def db(monkeypatch, tmp_path):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False)

    @contextmanager
    def fake_get_session():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    for module in (audio_service, preprocessing_service, db_session):
        monkeypatch.setattr(module, "get_session", fake_get_session)
    monkeypatch.setattr(Settings, "upload_dir", property(lambda self: tmp_path / "uploads"))
    monkeypatch.setattr(Settings, "heatmap_dir", property(lambda self: tmp_path / "heatmaps"))
    with fake_get_session() as s:
        s.add_all(Emotion(emotion_id=i, name=n, name_vi=v) for i, (n, v) in enumerate(zip(EMOTION_NAMES, EMOTION_NAMES_VI)))
        s.add_all([User(username="an", email="an@x.vn", password="h"), User(username="binh", email="b@x.vn", password="h")])
        s.add(MLModel(name="m", model_type="Transformer"))
        s.commit()
    return fake_get_session


def _user(db, username, role="User"):
    with db() as s:
        row = s.query(User).filter_by(username=username).one()
        return SessionUser(user_id=row.user_id, username=row.username, email=row.email, role=role)


def _wav(path, seconds=1.0, amp=0.3):
    t = np.arange(int(seconds * 16000)) / 16000
    sf.write(str(path), (amp * np.sin(2 * np.pi * 220 * t)).astype(np.float32), 16000)
    return str(path)


# ---------- UC02: kiểm tra tệp ----------
def test_validate_accepts_wav_and_returns_duration(tmp_path):
    assert audio_service.validate_upload(_wav(tmp_path / "a.wav", 1.5)) == pytest.approx(1.5, abs=0.01)


def test_validate_rejects_wrong_extension(tmp_path):
    bad = tmp_path / "a.txt"
    bad.write_text("không phải âm thanh")
    with pytest.raises(ValueError, match="WAV hoặc MP3"):
        audio_service.validate_upload(str(bad))


def test_validate_rejects_empty_missing_and_corrupt(tmp_path):
    empty = tmp_path / "empty.wav"
    empty.write_bytes(b"")
    corrupt = tmp_path / "corrupt.wav"
    corrupt.write_bytes(b"day khong phai tep wav hop le" * 20)
    for target, text in ((empty, "rỗng"), (corrupt, "giải mã"), (tmp_path / "khong-co.wav", "Không tìm thấy")):
        with pytest.raises(ValueError, match=text):
            audio_service.validate_upload(str(target))
    with pytest.raises(ValueError):
        audio_service.validate_upload("")


def test_validate_rejects_oversized_file(tmp_path, monkeypatch):
    monkeypatch.setattr(Settings, "max_upload_bytes", property(lambda self: 1000))
    with pytest.raises(ValueError, match="quá lớn"):
        audio_service.validate_upload(_wav(tmp_path / "big.wav", 1.0))


# ---------- UC02: lưu tệp ----------
def test_save_upload_copies_with_uuid_name_and_creates_row(db, tmp_path):
    user = _user(db, "an")
    saved = audio_service.save_upload(user, _wav(tmp_path / "giong-cua-toi.wav"))
    assert saved["filename"] == "giong-cua-toi.wav" and saved["user_id"] == user.user_id
    stored = tmp_path / "uploads"
    files = list(stored.iterdir())
    assert len(files) == 1 and files[0].name != "giong-cua-toi.wav" and files[0].suffix == ".wav"  # tên uuid, không tin tên client
    assert saved["file_path"] == str(files[0])


def test_save_upload_demo_session_is_not_stored(db, tmp_path):
    demo = SessionUser(user_id=-1, username="demo", email="d@x")
    assert audio_service.save_upload(demo, _wav(tmp_path / "a.wav")) is None
    assert not (tmp_path / "uploads").exists()
    with db() as s:
        assert s.query(AudioFile).count() == 0


def test_save_upload_validates_and_requires_login(db, tmp_path):
    with pytest.raises(ValueError):
        audio_service.save_upload(_user(db, "an"), str(tmp_path / "khong-co.wav"))
    with pytest.raises(PermissionDenied):
        audio_service.save_upload(None, _wav(tmp_path / "a.wav"))


def test_save_upload_removes_file_when_database_fails(db, tmp_path, monkeypatch):
    @contextmanager
    def broken():
        raise RuntimeError("db down")
        yield  # pragma: no cover

    monkeypatch.setattr(audio_service, "get_session", broken)
    with pytest.raises(RuntimeError):
        audio_service.save_upload(_user(db, "an"), _wav(tmp_path / "a.wav"))
    assert list((tmp_path / "uploads").iterdir()) == []  # không để tệp mồ côi


def test_get_audio_for_user_only_returns_own_or_any_for_admin(db, tmp_path):
    an, binh = _user(db, "an"), _user(db, "binh")
    saved = audio_service.save_upload(an, _wav(tmp_path / "a.wav"))
    assert audio_service.get_audio_for_user(an, saved["audio_id"])["audio_id"] == saved["audio_id"]
    assert audio_service.get_audio_for_user(binh, saved["audio_id"]) is None
    admin = _user(db, "binh", role="Admin")
    assert audio_service.get_audio_for_user(admin, saved["audio_id"]) is not None
    assert audio_service.get_audio_for_user(an, 999) is None


# ---------- UC03/UC04: đặc trưng, kết quả ----------
def _audio_row(db, user, tmp_path):
    return audio_service.save_upload(user, _wav(tmp_path / "a.wav"))["audio_id"]


def test_save_audio_features_inserts_then_updates(db, tmp_path):
    audio_id = _audio_row(db, _user(db, "an"), tmp_path)
    wave = np.zeros(48000, dtype=np.float32)
    wave[:16000] = 0.3 * np.sin(2 * np.pi * 220 * np.arange(16000) / 16000)
    preprocessing_service.save_audio_features(audio_id, wave, 1.0)
    preprocessing_service.save_audio_features(audio_id, wave, 1.2)
    with db() as s:
        rows = s.query(AudioFeature).all()
        assert len(rows) == 1 and rows[0].trimmed_duration == 1.2 and 100 < rows[0].f0_mean < 400 and rows[0].rms_mean > 0


def test_save_prediction_writes_prediction_and_eight_scores(db, tmp_path, monkeypatch):
    user = _user(db, "an")
    audio_id = _audio_row(db, user, tmp_path)
    monkeypatch.setitem(inference_service._state, "model_key", "1")
    probs = np.array([0.0, 0.0, 0.1, 0.0, 0.8, 0.1, 0.0, 1.0000001], dtype=np.float32)  # lệch float32 phải được kẹp về [0,1]
    probs[4] = 0.95
    pid = inference_service.save_prediction(user, audio_id, probs, "/x.png")
    with db() as s:
        pred = s.get(Prediction, pid)
        assert pred.audio_id == audio_id and pred.model_id == 1 and pred.emotion_id == 7 and pred.confidence == 1.0 and pred.heatmap_path == "/x.png"
        scores = s.query(PredictionScore).filter_by(prediction_id=pid).all()
        assert len(scores) == 8 and all(0 <= sc.probability <= 1 for sc in scores)


def test_save_prediction_rejects_other_users_audio_and_bad_shape(db, tmp_path, monkeypatch):
    an, binh = _user(db, "an"), _user(db, "binh")
    audio_id = _audio_row(db, an, tmp_path)
    monkeypatch.setitem(inference_service._state, "model_key", "1")
    with pytest.raises(ValueError, match="Không tìm thấy"):
        inference_service.save_prediction(binh, audio_id, np.full(8, 0.125), None)
    with pytest.raises(ValueError, match="8 xác suất"):
        inference_service.save_prediction(an, audio_id, np.full(5, 0.2), None)


def test_save_prediction_skips_when_model_is_not_registered(db, tmp_path, monkeypatch):
    user = _user(db, "an")
    audio_id = _audio_row(db, user, tmp_path)
    monkeypatch.setitem(inference_service._state, "model_key", None)  # chạy bằng MODEL_CHECKPOINT_PATH: chưa có dòng trong models
    assert inference_service.save_prediction(user, audio_id, np.full(8, 0.125), None) is None


# ---------- UC04: ảnh XAI ----------
def test_render_waveform_heatmap_writes_png(tmp_path):
    out = xai.render_waveform_heatmap(np.sin(np.linspace(0, 300, 48000)).astype(np.float32), np.random.default_rng(0).random(149), 1.8, str(tmp_path / "h.png"))
    assert out.endswith("h.png") and (tmp_path / "h.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_build_waveform_heatmap_uses_uuid_name_in_heatmap_dir(db, tmp_path):
    from services import xai_service

    path = xai_service.build_waveform_heatmap(np.zeros(48000, dtype=np.float32), np.ones(149), 3.0)
    assert (tmp_path / "heatmaps").samefile(__import__("pathlib").Path(path).parent) and path.endswith(".png")


# ---------- trang Phân tích ----------
def _run(db, monkeypatch, tmp_path, session):
    from ui.pages import analyze

    wave = (0.3 * np.sin(np.linspace(0, 400, 48000))).astype(np.float32)
    monkeypatch.setattr(analyze.preprocessing_service, "preprocess_with_duration", lambda path: (wave, 2.0))
    probs = np.array([0.02, 0.02, 0.03, 0.03, 0.80, 0.04, 0.03, 0.03], dtype=np.float32)
    monkeypatch.setattr(analyze.inference_service, "run_inference", lambda w: (probs, np.random.default_rng(1).random(149)))
    monkeypatch.setitem(inference_service._state, "model_key", "1")
    results = list(analyze.run_analysis(_wav(tmp_path / "in.wav"), None, "upload", session))
    return analyze, results


def test_analysis_saves_history_for_real_user(db, tmp_path, monkeypatch):
    analyze, results = _run(db, monkeypatch, tmp_path, _user(db, "an"))
    final = dict(zip(analyze.OUT_KEYS, results[-1]))
    assert final["col_result"]["visible"] is True and final["download"]["value"].endswith(".png")
    with db() as s:
        assert s.query(AudioFile).count() == 1 and s.query(AudioFeature).count() == 1
        pred = s.query(Prediction).one()
        assert pred.emotion_id == 4 and pred.heatmap_path == final["download"]["value"]
        assert s.query(PredictionScore).count() == 8


def test_analysis_does_not_save_for_demo_session(db, tmp_path, monkeypatch):
    analyze, results = _run(db, monkeypatch, tmp_path, SessionUser(user_id=-1, username="demo", email="d@x"))
    final = dict(zip(analyze.OUT_KEYS, results[-1]))
    assert "Phiên thử nghiệm" in final["banner"]["value"] and final["download"]["value"].endswith(".png")
    with db() as s:
        assert s.query(AudioFile).count() == 0 and s.query(Prediction).count() == 0


def test_analysis_rejects_invalid_file_before_processing(db, tmp_path, monkeypatch):
    from ui.pages import analyze

    bad = tmp_path / "a.txt"
    bad.write_text("x")
    results = list(analyze.run_analysis(str(bad), None, "upload", _user(db, "an")))
    assert len(results) == 1 and dict(zip(analyze.OUT_KEYS, results[0]))["col_input"]["visible"] is True


def test_analysis_still_shows_result_when_saving_fails(db, tmp_path, monkeypatch):
    analyze, _ = _run(db, monkeypatch, tmp_path, _user(db, "an"))

    def boom(*args, **kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(analyze, "_persist", boom)
    results = list(analyze.run_analysis(_wav(tmp_path / "in2.wav"), None, "upload", _user(db, "an")))
    final = dict(zip(analyze.OUT_KEYS, results[-1]))
    assert final["col_result"]["visible"] is True and "Chưa lưu được lịch sử" in final["banner"]["value"]
