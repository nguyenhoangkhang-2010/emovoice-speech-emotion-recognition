# UC06 (nhánh feat/admin-audio): quản lý dữ liệu âm thanh của mọi người dùng — xem, lọc, tìm kiếm, xóa sạch. SQLite trong bộ nhớ + thư mục tạm.
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401  (đăng ký bảng vào Base.metadata)
from core.config import Settings
from core.session import PermissionDenied, SessionUser
from db.base import Base
from ml.config import EMOTION_NAMES, EMOTION_NAMES_VI
from models.audio_feature import AudioFeature
from models.audio_file import AudioFile
from models.emotion import Emotion
from models.ml_model import MLModel
from models.prediction import Prediction
from models.prediction_score import PredictionScore
from models.system_log import SystemLog
from models.user import User
from services import admin_service as svc

NOW = datetime.now(timezone.utc)


@pytest.fixture()
def env(monkeypatch, tmp_path):
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

    monkeypatch.setattr(svc, "get_session", fake_get_session)
    for name in ("uploads", "heatmaps", "mel"):
        (tmp_path / name).mkdir()
    monkeypatch.setattr(Settings, "upload_dir", property(lambda self: tmp_path / "uploads"))
    monkeypatch.setattr(Settings, "heatmap_dir", property(lambda self: tmp_path / "heatmaps"))
    monkeypatch.setattr(Settings, "mel_dir", property(lambda self: tmp_path / "mel"))
    with fake_get_session() as s:
        s.add_all(Emotion(emotion_id=i, name=n, name_vi=v) for i, (n, v) in enumerate(zip(EMOTION_NAMES, EMOTION_NAMES_VI)))
        s.add(MLModel(name="m", model_type="T"))
        s.add_all([User(username="admin", email="a@x.vn", password="h", role="Admin"), User(username="anh", email="anh@x.vn", password="h"), User(username="binh", email="b@x.vn", password="h")])
        s.commit()
    return fake_get_session, tmp_path


def _admin(db):
    with db() as s:
        row = s.query(User).filter_by(username="admin").one()
        return SessionUser(user_id=row.user_id, username="admin", email="a@x.vn", role="Admin")


def _add(env, username, filename, emotions=(), days_ago=0, mel=False):
    """Một tệp (có thật trên đĩa) + các lượt phân tích theo thứ tự thời gian (lượt cuối là gần nhất); trả audio_id."""
    db, tmp = env
    audio_file = tmp / "uploads" / f"{filename}.wav"
    audio_file.write_bytes(b"RIFF")
    with db() as s:
        owner = s.query(User).filter_by(username=username).one()
        audio = AudioFile(user_id=owner.user_id, filename=filename, file_path=str(audio_file), duration=3.0, uploaded_at=NOW - timedelta(days=days_ago))
        s.add(audio)
        s.flush()
        mel_path = None
        if mel:
            mel_file = tmp / "mel" / f"{filename}.png"
            mel_file.write_bytes(b"png")
            mel_path = str(mel_file)
        s.add(AudioFeature(audio_id=audio.audio_id, trimmed_duration=2.0, mel_image_path=mel_path))
        for i, emotion in enumerate(emotions):
            heat = tmp / "heatmaps" / f"{filename}_{i}.png"
            heat.write_bytes(b"png")
            pred = Prediction(audio_id=audio.audio_id, model_id=1, emotion_id=EMOTION_NAMES.index(emotion), confidence=0.8, heatmap_path=str(heat), created_at=NOW + timedelta(minutes=i))
            pred.scores = [PredictionScore(emotion_id=k, probability=0.125) for k in range(8)]
            s.add(pred)
        s.commit()
        return audio.audio_id


def _count(db, model):
    with db() as s:
        return s.query(model).count()


# ---------- danh sách ----------
def test_list_shows_every_users_audio_newest_first_with_latest_result(env):
    db, _ = env
    _add(env, "anh", "cu.wav", ["angry"], days_ago=5)
    _add(env, "binh", "moi.wav", ["happy", "sad"], days_ago=0)  # phân tích hai lần: lấy kết quả gần nhất (sad)
    _add(env, "anh", "chua_phan_tich.wav", [], days_ago=2)
    rows, total = svc.list_all_audio(_admin(db))
    assert total == 3 and [r["file"] for r in rows] == ["moi.wav", "chua_phan_tich.wav", "cu.wav"]
    by_name = {r["file"]: r for r in rows}
    assert by_name["moi.wav"]["user"] == "binh" and by_name["moi.wav"]["emotion"] == "sad" and by_name["moi.wav"]["predictions"] == 2
    assert by_name["chua_phan_tich.wav"]["emotion"] is None and by_name["chua_phan_tich.wav"]["confidence"] is None and by_name["chua_phan_tich.wav"]["predictions"] == 0
    assert by_name["cu.wav"]["user"] == "anh" and by_name["cu.wav"]["duration"] == 3.0 and by_name["cu.wav"]["file_path"].endswith("cu.wav.wav")


def test_list_filters_by_filename_username_and_latest_emotion(env):
    db, _ = env
    admin = _admin(db)
    _add(env, "anh", "cuoc_goi_01", ["angry"])
    _add(env, "anh", "tu_van_02", ["happy"])
    _add(env, "binh", "cuoc_goi_03", ["happy", "angry"])
    assert [r["file"] for r in svc.list_all_audio(admin, q="TU_VAN")[0]] == ["tu_van_02"]
    assert sorted(r["file"] for r in svc.list_all_audio(admin, q="binh")[0]) == ["cuoc_goi_03"]  # tìm theo tên người dùng
    assert sorted(r["file"] for r in svc.list_all_audio(admin, emotion="angry")[0]) == ["cuoc_goi_01", "cuoc_goi_03"]
    assert [r["file"] for r in svc.list_all_audio(admin, emotion="happy")[0]] == ["tu_van_02"]  # cuoc_goi_03 giờ là angry nên không khớp happy
    assert svc.list_all_audio(admin, q="cuoc", emotion="happy") == ([], 0)
    assert svc.list_all_audio(admin, q="%")[1] == 0  # '%' là ký tự thường


def test_list_paginates(env):
    db, _ = env
    for i in range(25):
        _add(env, "anh", f"tep_{i:02d}", ["happy"], days_ago=i)
    admin = _admin(db)
    page1, total = svc.list_all_audio(admin, page=1, page_size=10)
    page3, _ = svc.list_all_audio(admin, page=3, page_size=10)
    assert total == 25 and len(page1) == 10 and len(page3) == 5
    assert len({r["audio_id"] for p in (1, 2, 3) for r in svc.list_all_audio(admin, page=p, page_size=10)[0]}) == 25


# ---------- xóa ----------
def test_delete_removes_rows_and_files(env):
    db, tmp = env
    audio_id = _add(env, "anh", "se_xoa", ["angry", "sad"], mel=True)
    keep_id = _add(env, "binh", "giu_lai", ["happy"], mel=True)
    summary = svc.delete_audio(_admin(db), audio_id)
    assert summary == {"file": "se_xoa", "user": "anh", "predictions": 2, "files_removed": 4}  # 1 âm thanh + 2 ảnh XAI + 1 ảnh Mel
    with db() as s:
        assert s.get(AudioFile, audio_id) is None and s.get(AudioFeature, audio_id) is None
        assert s.query(Prediction).filter_by(audio_id=audio_id).count() == 0
        assert s.query(PredictionScore).count() == 8  # chỉ còn 8 điểm của mẫu giữ lại: không sót điểm của mẫu đã xóa
    assert not (tmp / "uploads" / "se_xoa.wav").exists() and not list((tmp / "heatmaps").glob("se_xoa_*")) and not (tmp / "mel" / "se_xoa.png").exists()
    assert (tmp / "uploads" / "giu_lai.wav").exists() and (tmp / "mel" / "giu_lai.png").exists()  # mẫu khác nguyên vẹn
    with db() as s:
        assert s.get(AudioFile, keep_id) is not None


def test_delete_writes_log_without_paths(env):
    db, tmp = env
    audio_id = _add(env, "anh", "se_xoa", ["angry"])
    admin = _admin(db)
    svc.delete_audio(admin, audio_id)
    with db() as s:
        logs = [r for r in s.query(SystemLog)]
    assert len(logs) == 1 and logs[0].level == "WARNING" and logs[0].user_id == admin.user_id
    assert "xóa mẫu âm thanh 'se_xoa' của anh (1 lượt phân tích)" in logs[0].message and str(tmp) not in logs[0].message


def test_delete_unknown_audio_is_rejected_and_second_delete_too(env):
    db, _ = env
    admin = _admin(db)
    audio_id = _add(env, "anh", "x", [])
    with pytest.raises(ValueError, match="Không tìm thấy"):
        svc.delete_audio(admin, 9999)
    svc.delete_audio(admin, audio_id)
    with pytest.raises(ValueError, match="Không tìm thấy"):
        svc.delete_audio(admin, audio_id)


def test_delete_never_touches_files_outside_storage(env, tmp_path_factory):
    db, _ = env
    outside = tmp_path_factory.mktemp("ngoai") / "quan_trong.txt"
    outside.write_text("không được xóa")
    audio_id = _add(env, "anh", "lech_duong_dan", ["angry"])
    with db() as s:
        s.get(AudioFile, audio_id).file_path = str(outside)  # CSDL bị sửa trỏ ra ngoài thư mục lưu trữ
        s.commit()
    summary = svc.delete_audio(_admin(db), audio_id)
    assert outside.exists() and outside.read_text() == "không được xóa"
    assert summary["files_removed"] == 1  # chỉ ảnh XAI trong thư mục lưu trữ bị xóa


def test_delete_tolerates_files_already_gone(env):
    db, tmp = env
    audio_id = _add(env, "anh", "mat_tep", ["angry"])
    (tmp / "uploads" / "mat_tep.wav").unlink()
    summary = svc.delete_audio(_admin(db), audio_id)
    assert summary["files_removed"] == 1 and _count(db, AudioFile) == 0  # dòng CSDL vẫn xóa dù tệp đã mất


def test_failed_database_delete_keeps_files(env, monkeypatch):
    db, tmp = env
    audio_id = _add(env, "anh", "giu_tep", ["angry"])

    @contextmanager
    def broken():
        with db() as s:
            s.commit = lambda: (_ for _ in ()).throw(RuntimeError("db down"))
            yield s

    monkeypatch.setattr(svc, "get_session", broken)
    with pytest.raises(RuntimeError):
        svc.delete_audio(_admin(db), audio_id)
    assert (tmp / "uploads" / "giu_tep.wav").exists()  # CSDL lỗi thì không được mất tệp
    monkeypatch.setattr(svc, "get_session", db)
    assert _count(db, AudioFile) == 1


def test_non_admin_cannot_list_or_delete(env):
    db, _ = env
    audio_id = _add(env, "anh", "x", [])
    with db() as s:
        row = s.query(User).filter_by(username="anh").one()
        user = SessionUser(user_id=row.user_id, username="anh", email="anh@x.vn", role="User")
    for call in (lambda: svc.list_all_audio(user), lambda: svc.delete_audio(user, audio_id)):
        with pytest.raises(PermissionDenied):
            call()
    assert _count(db, AudioFile) == 1
