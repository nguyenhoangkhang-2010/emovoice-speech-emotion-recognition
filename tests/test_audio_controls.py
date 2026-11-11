# Người dùng tự tải / xóa dữ liệu âm thanh của mình (history_service, trang Lịch sử) và admin tải từng tệp có ghi nhật ký (admin_service).
from contextlib import contextmanager
from datetime import datetime, timezone
from types import SimpleNamespace

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
from services import admin_service, history_service
from ui.components import downloads
from ui.pages import history

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

    monkeypatch.setattr(history_service, "get_session", fake_get_session)
    monkeypatch.setattr(admin_service, "get_session", fake_get_session)
    for name in ("uploads", "heatmaps", "mel"):
        (tmp_path / name).mkdir()
    monkeypatch.setattr(Settings, "upload_dir", property(lambda self: tmp_path / "uploads"))
    monkeypatch.setattr(Settings, "heatmap_dir", property(lambda self: tmp_path / "heatmaps"))
    monkeypatch.setattr(Settings, "mel_dir", property(lambda self: tmp_path / "mel"))
    with fake_get_session() as s:
        s.add_all(Emotion(emotion_id=i, name=n, name_vi=v) for i, (n, v) in enumerate(zip(EMOTION_NAMES, EMOTION_NAMES_VI)))
        s.add(MLModel(name="m", model_type="T"))
        s.add_all([User(username="admin", email="a@x.vn", password="h", role="Admin"), User(username="an", email="an@x.vn", password="h"), User(username="binh", email="b@x.vn", password="h")])
        s.commit()
    return fake_get_session, tmp_path


def _session(env, username):
    with env[0]() as s:
        row = s.query(User).filter_by(username=username).one()
        return SessionUser(user_id=row.user_id, username=username, email=row.email, role=row.role)


def _add(env, username, filename, emotions=("angry",)):
    """Một tệp (có thật trên đĩa) + lượt phân tích kèm ảnh XAI và ảnh Mel; trả (audio_id, prediction_id đầu tiên)."""
    db, tmp = env
    audio_file = tmp / "uploads" / f"{filename}.wav"
    audio_file.write_bytes(b"RIFF")
    mel_file = tmp / "mel" / f"{filename}.png"
    mel_file.write_bytes(b"png")
    with db() as s:
        owner = s.query(User).filter_by(username=username).one()
        audio = AudioFile(user_id=owner.user_id, filename=filename, file_path=str(audio_file), duration=3.0)
        s.add(audio)
        s.flush()
        s.add(AudioFeature(audio_id=audio.audio_id, mel_image_path=str(mel_file)))
        first = None
        for i, emotion in enumerate(emotions):
            heat = tmp / "heatmaps" / f"{filename}_{i}.png"
            heat.write_bytes(b"png")
            prediction = Prediction(audio_id=audio.audio_id, model_id=1, emotion_id=EMOTION_NAMES.index(emotion), confidence=0.8, heatmap_path=str(heat), created_at=NOW)
            s.add(prediction)
            s.flush()
            s.add_all(PredictionScore(prediction_id=prediction.prediction_id, emotion_id=k, probability=0.125) for k in range(8))
            first = first or prediction.prediction_id
        s.commit()
        return audio.audio_id, first


def _files(tmp):
    return sorted(p.name for folder in ("uploads", "heatmaps", "mel") for p in (tmp / folder).iterdir())


# ---------- người dùng tự xóa ----------
def test_user_deletes_own_record_with_every_trace(env):
    db, tmp = env
    an = _session(env, "an")
    _, pid = _add(env, "an", "cua_an", ["angry", "sad"])
    _add(env, "binh", "cua_binh", ["happy"])
    summary = history_service.delete_history_item(an, pid)
    assert summary == {"file": "cua_an", "predictions": 2, "files_removed": 4}  # 1 âm thanh + 2 ảnh XAI + 1 ảnh Mel
    assert _files(tmp) == ["cua_binh.png", "cua_binh.wav", "cua_binh_0.png"]
    with db() as s:
        assert s.query(AudioFile).count() == 1 and s.query(Prediction).count() == 1 and s.query(PredictionScore).count() == 8 and s.query(AudioFeature).count() == 1
        (log,) = s.query(SystemLog).all()
        assert (log.level, log.service, log.user_id) == ("INFO", "audio", an.user_id)
        assert log.message == "an xóa bản ghi 'cua_an' khỏi lịch sử của mình (2 lượt phân tích)" and str(tmp) not in log.message


def test_user_cannot_delete_someone_elses_record(env):
    db, tmp = env
    _, other = _add(env, "binh", "cua_binh")
    before = _files(tmp)
    with pytest.raises(ValueError, match="Không tìm thấy"):
        history_service.delete_history_item(_session(env, "an"), other)
    with pytest.raises(ValueError, match="Không tìm thấy"):
        history_service.delete_history_item(_session(env, "an"), 9999)
    with pytest.raises(ValueError, match="Không tìm thấy"):
        history_service.delete_history_item(SessionUser(user_id=-1, username="demo", email="d@x"), other)
    with pytest.raises(PermissionDenied):
        history_service.delete_history_item(None, other)
    assert _files(tmp) == before
    with db() as s:
        assert s.query(AudioFile).count() == 1 and s.query(SystemLog).count() == 0


def test_delete_all_history_only_removes_own_data(env):
    db, tmp = env
    an = _session(env, "an")
    _add(env, "an", "a1", ["angry"])
    _add(env, "an", "a2", ["sad", "happy"])
    _add(env, "binh", "b1", ["happy"])
    assert history_service.count_audio(an) == 2 and history_service.count_audio(_session(env, "binh")) == 1
    done = history_service.delete_all_history(an)
    assert done == {"audio_files": 2, "predictions": 3, "files_removed": 7}
    assert _files(tmp) == ["b1.png", "b1.wav", "b1_0.png"]
    with db() as s:
        assert s.query(AudioFile).filter_by(user_id=an.user_id).count() == 0 and s.query(AudioFile).count() == 1
        (log,) = s.query(SystemLog).all()
        assert log.message == "an xóa toàn bộ lịch sử của mình (2 mẫu âm thanh, 3 lượt phân tích)"
    assert history_service.delete_all_history(an) == {"audio_files": 0, "predictions": 0, "files_removed": 0}
    with db() as s:
        assert s.query(SystemLog).count() == 1  # lịch sử trống thì không ghi thêm dòng nhật ký
    assert history_service.delete_all_history(SessionUser(user_id=-1, username="demo", email="d@x"))["audio_files"] == 0


# ---------- admin tải tệp ----------
def test_admin_download_is_logged_as_warning_with_who_and_whose(env):
    db, _ = env
    audio_id, _ = _add(env, "an", "giong_an")
    admin = _session(env, "admin")
    admin_service.log_audio_download(admin, audio_id)
    with db() as s:
        (log,) = s.query(SystemLog).all()
        assert (log.level, log.service, log.user_id) == ("WARNING", "admin", admin.user_id)
        assert log.message == "admin tải tệp âm thanh 'giong_an' của an về máy"
    with pytest.raises(ValueError, match="Không tìm thấy"):
        admin_service.log_audio_download(admin, 9999)
    for who in (_session(env, "an"), None):
        with pytest.raises(PermissionDenied):
            admin_service.log_audio_download(who, audio_id)
    with db() as s:
        assert s.query(SystemLog).count() == 1  # lượt bị từ chối không ghi gì thêm


# ---------- bản sao để tải về ----------
def test_audio_copy_keeps_the_original_name_and_stays_inside_the_folder(tmp_path):
    src = tmp_path / "3f2a9c.wav"
    src.write_bytes(b"RIFFdata")
    out = downloads.audio_copy(str(src), "cuộc gọi 01", "audio_7", tmp_path / "xuat")
    assert out == str(tmp_path / "xuat" / "audio_7" / "cuộc gọi 01.wav") and open(out, "rb").read() == b"RIFFdata"  # thiếu đuôi thì lấy đuôi tệp thật
    evil = downloads.audio_copy(str(src), "../../ngoai/x.mp3", "audio_8", tmp_path / "xuat")
    assert evil == str(tmp_path / "xuat" / "audio_8" / "x.mp3")
    assert downloads.audio_copy(str(tmp_path / "khong-co.wav"), "a.wav", "audio_9", tmp_path / "xuat") is None
    assert downloads.audio_copy(None, "a.wav", "audio_9", tmp_path / "xuat") is None


# ---------- trang Lịch sử ----------
def _page():
    import gradio as gr

    with gr.Blocks() as demo:
        history.build(gr.State(None))
    return demo


def _handler(demo, name):
    return next(f.fn for f in demo.fns.values() if getattr(f.fn, "__name__", "") == name)


def test_history_page_has_download_and_delete_controls():
    import gradio as gr

    demo = _page()
    labels = {text for b in demo.blocks.values() if isinstance(b, (gr.Button, gr.DownloadButton)) for text in (getattr(b, "value", None), getattr(b, "label", None))}
    assert {"Tải tệp âm thanh", "Xóa toàn bộ lịch sử", "Xác nhận xóa", "Hủy"} <= labels
    assert "Xóa bản ghi" not in labels  # xóa từng bản ghi bằng biểu tượng thùng rác trên dòng, không có nút trong ngăn chi tiết
    assert history.TABLE_HEADERS[-1] == "Xóa" and history.DELETE_COL == 6 and len(history.EMPTY_TABLE[0]) == 7 and len(history._detail_empty()) == 10


def test_history_delete_asks_first_and_only_then_deletes(monkeypatch, tmp_path):
    demo = _page()
    user = SessionUser(user_id=5, username="an", email="a@x.vn")
    calls, notes = [], []
    monkeypatch.setattr(history.gr, "Info", lambda m: notes.append(("info", m)))
    monkeypatch.setattr(history.gr, "Warning", lambda m: notes.append(("warn", m)))
    monkeypatch.setattr(history.history_service, "count_audio", lambda s: 3)
    monkeypatch.setattr(history.history_service, "delete_history_item", lambda s, pid: calls.append(("one", pid)) or {"file": "a.wav", "predictions": 1, "files_removed": 3})
    monkeypatch.setattr(history.history_service, "delete_all_history", lambda s: calls.append(("all",)) or {"audio_files": 3, "predictions": 3, "files_removed": 9})
    monkeypatch.setattr(history.history_service, "list_history", lambda *a, **k: ([], 0))
    monkeypatch.setattr(history.history_service, "summarize_history", lambda *a, **k: {"total": 0, "avg_confidence": 0.0})
    monkeypatch.setattr(history.history_service, "export_history_csv", lambda *a, **k: "")
    monkeypatch.setattr(history, "_export_dir", lambda: tmp_path)

    on_select, ask_all, confirm = _handler(demo, "on_select"), _handler(demo, "ask_all"), _handler(demo, "on_confirm")
    rows = [{"id": 7, "file": "giong.wav"}, {"id": 8, "file": "khac.wav"}]
    out = on_select(rows, user, SimpleNamespace(index=[0, history.DELETE_COL]))  # bấm thùng rác của dòng đầu
    modal, question, pending = out[-3:]
    assert modal["visible"] is True and "giong.wav" in question and pending == {"kind": "one", "id": 7} and calls == []  # hỏi trước, chưa xóa gì
    assert all(item == {"__type__": "update"} for item in out[:-3])  # ngăn chi tiết giữ nguyên
    monkeypatch.setattr(history, "_detail", lambda s, pid: history._detail_empty())
    out = on_select(rows, user, SimpleNamespace(index=[1, 0]))  # bấm cột khác: mở chi tiết, không hỏi xóa
    assert out[-3:] == [{"__type__": "update"}] * 3 and calls == []
    modal, question, pending = ask_all(user)
    assert modal["visible"] is True and "3 bản ghi" in question and pending == {"kind": "all"} and calls == []

    out = confirm({"kind": "one", "id": 7}, 10, user, "", "Tất cả cảm xúc", "30 ngày qua", "")
    assert calls == [("one", 7)] and out[0]["visible"] is False and out[1] is None and notes[-1] == ("info", 'Đã xóa bản ghi "a.wav".')
    confirm({"kind": "all"}, 10, user, "", "Tất cả cảm xúc", "30 ngày qua", "")
    assert calls[-1] == ("all",) and notes[-1] == ("info", "Đã xóa 3 bản ghi trong lịch sử của bạn.")
    n = len(calls)
    out = confirm(None, 10, user, "", "Tất cả cảm xúc", "30 ngày qua", "")
    assert len(calls) == n and out[0]["visible"] is False  # không có yêu cầu chờ thì không xóa gì


def test_history_delete_of_an_already_deleted_record_only_warns(monkeypatch, tmp_path):
    demo = _page()
    user = SessionUser(user_id=5, username="an", email="a@x.vn")
    notes = []
    monkeypatch.setattr(history.gr, "Warning", lambda m: notes.append(m))
    monkeypatch.setattr(history.gr, "Info", lambda m: notes.append(m))

    def gone(session, pid):
        raise ValueError(history_service.MSG_RECORD_NOT_FOUND)

    monkeypatch.setattr(history.history_service, "delete_history_item", gone)
    monkeypatch.setattr(history.history_service, "list_history", lambda *a, **k: ([], 0))
    monkeypatch.setattr(history.history_service, "summarize_history", lambda *a, **k: {"total": 0, "avg_confidence": 0.0})
    monkeypatch.setattr(history.history_service, "export_history_csv", lambda *a, **k: "")
    monkeypatch.setattr(history, "_export_dir", lambda: tmp_path)
    out = _handler(demo, "on_confirm")({"kind": "one", "id": 7}, 10, user, "", "Tất cả cảm xúc", "30 ngày qua", "")
    assert notes == [history_service.MSG_RECORD_NOT_FOUND] and out[0]["visible"] is False
