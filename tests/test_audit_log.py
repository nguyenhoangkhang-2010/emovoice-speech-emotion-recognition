# Nhật ký hệ thống (feat/audit-log): phân tích, lỗi, tệp bị từ chối, nạp mô hình, thay đổi tài khoản, lọc theo dịch vụ. SQLite trong bộ nhớ.
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401  (đăng ký bảng vào Base.metadata)
from core.config import Settings
from core.session import SessionUser
from db import session as db_session
from db.base import Base
from ml.config import EMOTION_NAMES, EMOTION_NAMES_VI
from models.emotion import Emotion
from models.ml_model import MLModel
from models.system_log import SystemLog
from models.user import User
from services import account_service, admin_service, audio_service, audit_service, baseline_service, inference_service, preprocessing_service
from ui.pages import analyze

sf = pytest.importorskip("soundfile")


def _rows(factory, **filters):
    with factory() as s:
        return [(r.level, r.service, r.message, r.user_id) for r in s.query(SystemLog).filter_by(**filters).order_by(SystemLog.log_id)]


# ---------- audit_service ----------
def test_log_writes_a_row_for_real_user_and_none_for_demo(audit_db):
    audit_service.log("INFO", "inference", "một sự kiện", 7)
    audit_service.log("WARNING", "audio", "của phiên thử", SessionUser(user_id=-1, username="demo", email="d@x"))
    audit_service.log("ERROR", "model", "không gắn người dùng")
    audit_service.log("INFO", "auth", "đối tượng phiên thật", SessionUser(user_id=9, username="an", email="a@x"))
    assert _rows(audit_db) == [
        ("INFO", "inference", "một sự kiện", 7),
        ("WARNING", "audio", "của phiên thử", None),  # user_id <= 0 không có khóa ngoại để gắn
        ("ERROR", "model", "không gắn người dùng", None),
        ("INFO", "auth", "đối tượng phiên thật", 9),
    ]


def test_log_cleans_control_characters_and_truncates():
    assert audit_service.clean("tên\ntệp\r\n\tlạ.wav") == "tên tệp lạ.wav"  # tên tệp do người dùng đặt không được làm vỡ dòng nhật ký
    assert audit_service.clean("x" * 900).endswith("…") and len(audit_service.clean("x" * 900)) == audit_service.MESSAGE_MAX
    assert audit_service.clean("ngắn") == "ngắn"


def test_log_never_raises_even_when_database_or_level_is_bad(audit_db, monkeypatch):
    audit_service.log("NGUY_HIEM", "x", "mức sai")  # mức không hợp lệ: bỏ qua, không ném lỗi
    assert _rows(audit_db) == []

    @contextmanager
    def broken():
        raise RuntimeError("db down")
        yield  # pragma: no cover

    monkeypatch.setattr(audit_service, "get_session", broken)
    audit_service.log("INFO", "x", "CSDL hỏng")  # nhật ký là việc phụ: không được làm hỏng thao tác của người dùng


# ---------- luồng phân tích ----------
MAIN = np.array([0.02, 0.02, 0.03, 0.03, 0.80, 0.04, 0.03, 0.03])


@pytest.fixture()
def env(monkeypatch, tmp_path):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False)

    @contextmanager
    def fake_get_session():
        s = factory()
        try:
            yield s
        finally:
            s.close()

    for module in (audio_service, preprocessing_service, db_session, account_service, admin_service):
        monkeypatch.setattr(module, "get_session", fake_get_session)
    for name, attr in (("uploads", "upload_dir"), ("heatmaps", "heatmap_dir"), ("mel", "mel_dir")):
        monkeypatch.setattr(Settings, attr, property(lambda self, n=name: tmp_path / n))
    with fake_get_session() as s:
        s.add_all(Emotion(emotion_id=i, name=n, name_vi=v) for i, (n, v) in enumerate(zip(EMOTION_NAMES, EMOTION_NAMES_VI)))
        s.add(MLModel(name="M", model_type="T"))
        s.add_all([User(username="anh", email="anh@x.vn", password="h", role="Admin"), User(username="binh", email="b@x.vn", password="h")])
        s.commit()
    wave = (0.3 * np.sin(np.linspace(0, 400, 48000))).astype(np.float32)
    monkeypatch.setattr(analyze.preprocessing_service, "preprocess_with_duration", lambda p: (wave, 2.0))
    monkeypatch.setattr(analyze.inference_service, "run_inference", lambda w: (MAIN, np.random.default_rng(1).random(149)))
    monkeypatch.setattr(analyze.xai_service, "build_waveform_heatmap", lambda *a: None)
    monkeypatch.setattr(analyze.xai_service, "build_mel_attention", lambda *a: None)
    monkeypatch.setitem(inference_service._state, "model_key", "1")
    monkeypatch.setitem(inference_service._state, "name", "M")
    monkeypatch.setitem(inference_service._state, "last_latency_ms", 85.4)
    return fake_get_session, tmp_path


def _wav(path):
    t = np.arange(24000) / 16000
    sf.write(str(path), (0.3 * np.sin(2 * np.pi * 220 * t)).astype(np.float32), 16000)
    return str(path)


def _user(env, username):
    with env[0]() as s:
        row = s.query(User).filter_by(username=username).one()
        return SessionUser(user_id=row.user_id, username=row.username, email=row.email, role=row.role)


def _analyze(env, session, name="giong_noi.wav", **kwargs):
    audio = _wav(env[1] / name)
    return list(analyze.run_analysis(audio, None, "upload", session, **kwargs))


def test_successful_analysis_is_logged_with_file_result_model_and_timing(env, audit_db):
    me = _user(env, "binh")
    results = _analyze(env, me)
    assert dict(zip(analyze.OUT_KEYS, results[-1]))["col_result"]["visible"] is True
    (level, service, message, uid), = _rows(audit_db, service="inference")
    assert level == "INFO" and uid == me.user_id
    assert message.startswith("Phân tích giong_noi.wav → Tức giận 80.0% (M, suy luận 85 ms, tổng ") and "[phiên thử" not in message
    upload = _rows(env[0], service="audio")  # lượt tải lên ghi cùng giao dịch với việc lưu tệp
    assert [(r[0], r[3]) for r in upload] == [("INFO", me.user_id)] and "binh tải lên giong_noi.wav (1.5 s)" == upload[0][2]


def test_demo_session_analysis_is_logged_but_flagged_unsaved(env, audit_db):
    _analyze(env, SessionUser(user_id=-1, username="demo", email="d@x"))
    (_, _, message, uid), = _rows(audit_db, service="inference")
    assert uid is None and message.endswith("[phiên thử, không lưu]")
    assert _rows(env[0], service="audio") == []  # không lưu tệp thì không có dòng "tải lên"


def test_rejected_file_is_logged_as_warning(env, audit_db):
    bad = env[1] / "tai_lieu.txt"
    bad.write_text("không phải âm thanh")
    me = _user(env, "binh")
    results = list(analyze.run_analysis(str(bad), None, "upload", me))
    assert len(results) == 1  # dừng ngay ở bước kiểm tra
    (level, service, message, uid), = _rows(audit_db, service="audio")
    assert (level, uid) == ("WARNING", me.user_id) and message.startswith("Tệp bị từ chối (tai_lieu.txt): Định dạng không được hỗ trợ")


def test_decode_failure_and_missing_model_are_logged_as_errors(env, audit_db, monkeypatch):
    me = _user(env, "binh")

    def cannot_decode(path):
        raise RuntimeError("giải mã lỗi")

    monkeypatch.setattr(analyze.preprocessing_service, "preprocess_with_duration", cannot_decode)
    _analyze(env, me, "hong.wav")
    assert _rows(audit_db, service="preprocess") == [("ERROR", "preprocess", "Không đọc được âm thanh (hong.wav)", me.user_id)]

    wave = np.zeros(48000, dtype=np.float32)
    monkeypatch.setattr(analyze.preprocessing_service, "preprocess_with_duration", lambda p: (wave, 2.0))

    def no_model(w):
        raise inference_service.ModelNotReady("Chưa có mô hình đang dùng.")

    monkeypatch.setattr(analyze.inference_service, "run_inference", no_model)
    _analyze(env, me, "ok.wav")
    (level, _, message, _), = _rows(audit_db, service="inference")
    assert level == "ERROR" and message == "Không phân tích được (ok.wav): Chưa có mô hình đang dùng."


def test_history_save_failure_is_logged_and_result_still_shown(env, audit_db, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(analyze, "_persist", boom)
    results = _analyze(env, _user(env, "binh"))
    assert dict(zip(analyze.OUT_KEYS, results[-1]))["col_result"]["visible"] is True
    assert ("ERROR", "audio", "Không lưu được lịch sử cho giong_noi.wav") in [r[:3] for r in _rows(audit_db, service="audio")]


def test_baseline_failures_are_logged_as_warnings(env, audit_db, monkeypatch):
    def not_ready(path):
        raise baseline_service.BaselineNotReady("Chưa đăng ký baseline Random Forest.")

    monkeypatch.setattr(analyze.baseline_service, "run_random_forest", not_ready)
    _analyze(env, _user(env, "binh"), compare_rf=True)
    assert _rows(audit_db, service="baseline")[0][:3] == ("WARNING", "baseline", "Không so sánh được với Random Forest: Chưa đăng ký baseline Random Forest.")

    def unexpected(path):
        raise RuntimeError("lỗi lạ")

    monkeypatch.setattr(analyze.baseline_service, "run_random_forest", unexpected)
    _analyze(env, _user(env, "binh"), "hai.wav", compare_rf=True)
    assert _rows(audit_db, service="baseline")[-1][0] == "ERROR"


# ---------- nạp mô hình ----------
def test_model_load_is_logged_once_not_on_every_analysis(audit_db, monkeypatch, tmp_path):
    from ml import inference

    ckpt = tmp_path / "m.pt"
    ckpt.write_bytes(b"x")
    loaded = {"yes": False}
    monkeypatch.setattr(inference_service, "_resolve_checkpoint", lambda: ("DistilHuBERT + LoRA", str(ckpt), "1"))
    monkeypatch.setattr(inference, "loaded_info", lambda: {"loaded": loaded["yes"], "path": str(ckpt) if loaded["yes"] else None, "device": "cpu"})

    def fake_predict(wave, path):
        loaded["yes"] = True  # lần gọi đầu nạp mô hình vào bộ nhớ
        return None, MAIN, np.zeros(149)

    monkeypatch.setattr(inference, "predict", fake_predict)
    inference_service.run_inference(np.zeros(48000, dtype=np.float32))
    inference_service.run_inference(np.zeros(48000, dtype=np.float32))
    rows = _rows(audit_db, service="model")
    assert len(rows) == 1 and rows[0][0] == "INFO" and rows[0][2].startswith("Nạp mô hình DistilHuBERT + LoRA lên cpu")


# ---------- thay đổi tài khoản ----------
def test_profile_change_logs_only_field_names_never_values(env):
    me = _user(env, "binh")
    account_service.update_profile(me, "Nguyễn Bình", "b@x.vn")  # chỉ đổi họ tên (email giữ nguyên)
    account_service.update_profile(me, "Nguyễn Bình", "moi@x.vn")  # chỉ đổi email
    account_service.update_profile(me, "Nguyễn Bình", "moi@x.vn")  # không đổi gì
    rows = _rows(env[0], service="account")
    assert [r[2] for r in rows] == ["binh cập nhật hồ sơ (họ tên)", "binh cập nhật hồ sơ (email)"]  # lần thứ ba không để lại dòng nào
    assert all(r[0] == "INFO" and r[3] == me.user_id for r in rows)
    assert not any("moi@x.vn" in r[2] or "Nguyễn" in r[2] for r in rows)


def test_password_change_and_wrong_current_password_are_logged(env, monkeypatch):
    monkeypatch.setattr(account_service, "hash_password", lambda plain: f"h:{plain}")
    monkeypatch.setattr(account_service, "verify_password", lambda plain, hashed: hashed == f"h:{plain}")
    with env[0]() as s:
        s.query(User).filter_by(username="binh").one().password = "h:matkhau-cu-123"
        s.commit()
    me = _user(env, "binh")
    with pytest.raises(ValueError, match="không đúng"):
        account_service.change_password(me, "sai-mat-khau", "matkhau-moi-456", "matkhau-moi-456")
    account_service.change_password(me, "matkhau-cu-123", "matkhau-moi-456", "matkhau-moi-456")
    rows = _rows(env[0], service="account")
    assert [(r[0], r[2]) for r in rows] == [("WARNING", "binh nhập sai mật khẩu hiện tại khi đổi mật khẩu"), ("INFO", "binh đổi mật khẩu")]
    assert not any("matkhau" in r[2] for r in rows)  # không bao giờ ghi mật khẩu


# ---------- lọc theo dịch vụ ở trang nhật ký ----------
def test_admin_can_filter_logs_by_service(env):
    admin = _user(env, "anh")
    now = datetime.now(timezone.utc)
    with env[0]() as s:
        s.add_all(
            [
                SystemLog(level="INFO", service="inference", message="Phân tích a.wav", created_at=now),
                SystemLog(level="INFO", service="auth", message="Đăng nhập", created_at=now - timedelta(minutes=1)),
                SystemLog(level="ERROR", service="inference", message="Lỗi", created_at=now - timedelta(minutes=2)),
            ]
        )
        s.commit()
    assert [r["message"] for r in admin_service.list_logs(admin, service="inference")[0]] == ["Phân tích a.wav", "Lỗi"]
    assert [r["message"] for r in admin_service.list_logs(admin, service="inference", level="ERROR")[0]] == ["Lỗi"]  # kết hợp với bộ lọc mức
    assert admin_service.list_logs(admin, service="model") == ([], 0)
    assert admin_service.list_logs(admin, service="")[1] == 3  # trống = không lọc
    with pytest.raises(ValueError, match="Dịch vụ không hợp lệ"):
        admin_service.list_logs(admin, service="khong-co")
    assert {"auth", "inference", "audio", "model", "xai", "baseline", "preprocess", "account", "admin"} == set(admin_service.LOG_SERVICES)
