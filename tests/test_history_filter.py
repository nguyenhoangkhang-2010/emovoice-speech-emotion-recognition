# UC05 lịch sử + danh sách mẫu âm thanh có lọc/tìm kiếm (đề cương thang điểm mục 6). SQLite trong bộ nhớ.
import csv
import io
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401  (đăng ký bảng vào Base.metadata)
from core.session import PermissionDenied, SessionUser
from db.base import Base
from ml.config import EMOTION_NAMES, EMOTION_NAMES_VI
from models.audio_file import AudioFile
from models.emotion import Emotion
from models.ml_model import MLModel
from models.prediction import Prediction
from models.prediction_score import PredictionScore
from models.user import User
from services import history_service as svc

NOW = datetime.now(timezone.utc)


@pytest.fixture()
def db(monkeypatch):
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
    with fake_get_session() as s:
        s.add_all(Emotion(emotion_id=i, name=n, name_vi=v) for i, (n, v) in enumerate(zip(EMOTION_NAMES, EMOTION_NAMES_VI)))
        s.add_all([User(username="anh", email="a@x.vn", password="h"), User(username="binh", email="b@x.vn", password="h")])
        s.add(MLModel(name="DistilHuBERT + LoRA", model_type="Transformer"))
        s.commit()
    return fake_get_session


def _user(db, username):
    with db() as s:
        row = s.query(User).filter_by(username=username).one()
        return SessionUser(user_id=row.user_id, username=row.username, email=row.email)


def _add(db, username, filename, emotion, confidence, days_ago=0, duration=3.0):
    """Một tệp + một lượt phân tích; trả prediction_id."""
    with db() as s:
        owner = s.query(User).filter_by(username=username).one()
        audio = AudioFile(user_id=owner.user_id, filename=filename, file_path=f"/up/{filename}", duration=duration, uploaded_at=NOW - timedelta(days=days_ago))
        s.add(audio)
        s.flush()
        eid = EMOTION_NAMES.index(emotion)
        pred = Prediction(audio_id=audio.audio_id, model_id=1, emotion_id=eid, confidence=confidence, heatmap_path=f"/h/{filename}.png", created_at=NOW - timedelta(days=days_ago))
        pred.scores = [PredictionScore(emotion_id=i, probability=confidence if i == eid else (1 - confidence) / 7) for i in range(8)]
        s.add(pred)
        s.commit()
        return pred.prediction_id


@pytest.fixture()
def data(db):
    ids = {
        "giận": _add(db, "anh", "cuoc_goi_01.wav", "angry", 0.9, days_ago=0),
        "vui": _add(db, "anh", "tu_van_02.wav", "happy", 0.8, days_ago=3),
        "buồn": _add(db, "anh", "phan_nan_03.wav", "sad", 0.7, days_ago=20),
        "cũ": _add(db, "anh", "khao_sat_04.wav", "angry", 0.6, days_ago=90),
        "của_bình": _add(db, "binh", "cuoc_goi_bi_mat.wav", "angry", 0.99, days_ago=0),
    }
    return ids


def _names(rows):
    return [r["file"] for r in rows]


def test_history_returns_only_own_records_newest_first(db, data):
    rows, total = svc.list_history(_user(db, "anh"))
    assert total == 4 and _names(rows) == ["cuoc_goi_01.wav", "tu_van_02.wav", "phan_nan_03.wav", "khao_sat_04.wav"]
    assert "cuoc_goi_bi_mat.wav" not in _names(rows)  # không thấy bản ghi của người khác
    first = rows[0]
    assert first["emotion"] == "angry" and first["confidence"] == 0.9 and first["model"] == "DistilHuBERT + LoRA" and first["duration"] == 3.0 and first["id"] == data["giận"]


def test_history_filters_by_emotion_days_and_filename(db, data):
    me = _user(db, "anh")
    assert _names(svc.list_history(me, emotion="angry")[0]) == ["cuoc_goi_01.wav", "khao_sat_04.wav"]
    assert _names(svc.list_history(me, days=7)[0]) == ["cuoc_goi_01.wav", "tu_van_02.wav"]
    assert _names(svc.list_history(me, days=30)[0]) == ["cuoc_goi_01.wav", "tu_van_02.wav", "phan_nan_03.wav"]
    assert _names(svc.list_history(me, q="TU_VAN")[0]) == ["tu_van_02.wav"]  # không phân biệt hoa/thường
    assert _names(svc.list_history(me, q="  tu_van ")[0]) == ["tu_van_02.wav"]  # bỏ khoảng trắng đầu cuối
    assert _names(svc.list_history(me, q="tuxvan")[0]) == []  # '_' không khớp ký tự bất kỳ
    assert _names(svc.list_history(me, emotion="angry", days=30, q="cuoc")[0]) == ["cuoc_goi_01.wav"]  # kết hợp nhiều bộ lọc
    assert svc.list_history(me, emotion="fearful") == ([], 0)


def test_search_treats_percent_and_underscore_literally(db):
    _add(db, "anh", "ghi_am_100%.wav", "happy", 0.8)
    _add(db, "anh", "ghixam100.wav", "happy", 0.8)
    me = _user(db, "anh")
    assert _names(svc.list_history(me, q="_")[0]) == ["ghi_am_100%.wav"]
    assert _names(svc.list_history(me, q="%")[0]) == ["ghi_am_100%.wav"]
    assert svc.list_history(me, q="%%")[1] == 0


def test_history_pagination(db):
    for i in range(25):
        _add(db, "anh", f"tep_{i:02d}.wav", "happy", 0.5 + i / 100, days_ago=0)
    me = _user(db, "anh")
    page1, total = svc.list_history(me, page=1, page_size=10)
    page3, _ = svc.list_history(me, page=3, page_size=10)
    page4, _ = svc.list_history(me, page=4, page_size=10)
    assert total == 25 and len(page1) == 10 and len(page3) == 5 and page4 == []
    assert svc.list_history(me, page=1, page_size=50)[0].__len__() == 25
    assert len({r["id"] for r in page1} | {r["id"] for r in svc.list_history(me, page=2, page_size=10)[0]} | {r["id"] for r in page3}) == 25  # các trang không chồng lấn
    assert svc.list_history(me, page=0, page_size=10)[0] == page1  # trang < 1 coi như trang 1
    assert len(svc.list_history(me, page=1, page_size=10_000)[0]) == 25  # chặn cỡ trang quá lớn (tối đa 100)


def test_summary_covers_all_matches_not_just_one_page(db, data):
    me = _user(db, "anh")
    assert svc.summarize_history(me) == {"total": 4, "avg_confidence": pytest.approx((0.9 + 0.8 + 0.7 + 0.6) / 4)}
    assert svc.summarize_history(me, emotion="angry")["avg_confidence"] == pytest.approx(0.75)
    assert svc.summarize_history(me, q="khong-co") == {"total": 0, "avg_confidence": 0.0}


def test_detail_has_all_probabilities_and_paths(db, data):
    detail = svc.get_history_detail(_user(db, "anh"), data["giận"])
    assert len(detail["probs"]) == 8 and detail["probs"][EMOTION_NAMES.index("angry")] == 0.9 and sum(detail["probs"]) == pytest.approx(1.0)
    assert detail["heatmap_path"] == "/h/cuoc_goi_01.wav.png" and detail["audio_path"] == "/up/cuoc_goi_01.wav" and detail["emotion"] == "angry"


def test_detail_is_none_for_other_users_and_unknown_ids(db, data):
    assert svc.get_history_detail(_user(db, "anh"), data["của_bình"]) is None  # như 404: không lộ bản ghi của người khác
    assert svc.get_history_detail(_user(db, "binh"), data["giận"]) is None
    assert svc.get_history_detail(_user(db, "anh"), 99999) is None


def test_admin_sees_only_own_history_here(db, data):
    with db() as s:
        s.query(User).filter_by(username="binh").one().role = "Admin"
        s.commit()
    admin = SessionUser(user_id=_user(db, "binh").user_id, username="binh", email="b@x.vn", role="Admin")
    assert _names(svc.list_history(admin)[0]) == ["cuoc_goi_bi_mat.wav"]
    assert svc.get_history_detail(admin, data["giận"]) is None  # mẫu của người khác thuộc trang Quản lý dữ liệu âm thanh


def test_login_required_and_demo_session_is_empty(db, data):
    demo = SessionUser(user_id=-1, username="demo", email="d@x")
    assert svc.list_history(demo) == ([], 0) and svc.summarize_history(demo) == {"total": 0, "avg_confidence": 0.0}
    assert svc.get_history_detail(demo, 1) is None and svc.list_audio_samples(demo) == []
    assert svc.export_history_csv(demo).strip("﻿\r\n").count("\n") == 0  # chỉ có dòng tiêu đề
    for call in (svc.list_history, svc.summarize_history, svc.list_audio_samples, svc.export_history_csv):
        with pytest.raises(PermissionDenied):
            call(None)
    with pytest.raises(PermissionDenied):
        svc.get_history_detail(None, 1)


def test_audio_samples_show_latest_result_and_filter(db, data):
    me = _user(db, "anh")
    with db() as s:
        audio_id = s.query(AudioFile).filter_by(filename="cuoc_goi_01.wav").one().audio_id
        s.add(Prediction(audio_id=audio_id, model_id=1, emotion_id=EMOTION_NAMES.index("sad"), confidence=0.55, created_at=NOW + timedelta(minutes=5)))  # phân tích lại lần 2
        s.add(AudioFile(user_id=me.user_id, filename="chua_phan_tich.wav", file_path="/up/x.wav", duration=2.0, uploaded_at=NOW - timedelta(days=1)))
        s.commit()
    samples = svc.list_audio_samples(me)
    assert [x["file"] for x in samples] == ["cuoc_goi_01.wav", "chua_phan_tich.wav", "tu_van_02.wav", "phan_nan_03.wav", "khao_sat_04.wav"]
    by_name = {x["file"]: x for x in samples}
    assert by_name["cuoc_goi_01.wav"]["emotion"] == "sad" and by_name["cuoc_goi_01.wav"]["confidence"] == 0.55  # lấy kết quả gần nhất
    assert by_name["chua_phan_tich.wav"]["emotion"] is None and by_name["chua_phan_tich.wav"]["confidence"] is None
    assert [x["file"] for x in svc.list_audio_samples(me, q="tu_van")] == ["tu_van_02.wav"]
    assert [x["file"] for x in svc.list_audio_samples(me, emotion="happy")] == ["tu_van_02.wav"]
    assert "cuoc_goi_bi_mat.wav" not in by_name


def test_csv_export_matches_filters_and_neutralizes_formulas(db, data):
    _add(db, "anh", "=HYPERLINK(\"http://x\").wav", "happy", 0.5, days_ago=1)
    me = _user(db, "anh")
    text = svc.export_history_csv(me, days=7)
    assert text.startswith("﻿")
    rows = list(csv.reader(io.StringIO(text.lstrip("﻿"))))
    assert rows[0] == svc.CSV_HEADER
    names = [r[0] for r in rows[1:]]
    assert names == ["cuoc_goi_01.wav", "'=HYPERLINK(\"http://x\").wav", "tu_van_02.wav"]  # đúng bộ lọc 7 ngày, không có của người khác; công thức bị vô hiệu
    assert rows[1][2] == "happy" or rows[1][2] == "angry"
    assert rows[1][3] == "90.0" and rows[1][1] == "3.00"
