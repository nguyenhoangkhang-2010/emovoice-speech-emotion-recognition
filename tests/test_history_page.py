# Trang Lịch sử (UC05, phần giao diện): đổi nhãn bộ lọc, định dạng hiển thị, báo cáo JSON, xử lý khi chưa có dữ liệu hoặc CSDL lỗi.
import json
from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import OperationalError

from core.session import SessionUser
from ui import i18n_vi as T
from ui.pages import history


def test_filter_labels_map_to_service_arguments():
    assert history._emotion_key(T.EMOTION_VI["angry"]) == "angry"
    assert history._emotion_key(T.HISTORY_ALL_EMOTIONS) is None and history._emotion_key(None) is None
    assert [history._days(label) for label in T.HISTORY_TIME_CHOICES] == [7, 30, None]


def test_duration_and_time_formatting():
    assert history._fmt_duration(3.0) == "00:03.00" and history._fmt_duration(65.5) == "01:05.50"
    naive_utc = datetime(2026, 10, 17, 9, 30)  # SQLite trả datetime không múi giờ: phải coi là UTC rồi đổi sang giờ máy
    aware = naive_utc.replace(tzinfo=timezone.utc)
    assert history._fmt_time(naive_utc) == history._fmt_time(aware)
    assert len(history._fmt_time(aware)) == len("09:30 - 17/10/2026")


def test_json_report_has_probabilities_and_no_server_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "_export_dir", lambda: tmp_path)
    detail = {
        "id": 7, "file": "a.wav", "duration": 3.0, "emotion": "angry", "confidence": 0.9, "model": "m",
        "created_at": datetime(2026, 10, 17, 9, 30, tzinfo=timezone.utc), "probs": [0.01, 0.02, 0.01, 0.02, 0.9, 0.02, 0.01, 0.01],
        "heatmap_path": "/secret/server/heat.png", "audio_path": "/secret/server/a.wav",
    }
    text = open(history._write_json(detail), encoding="utf-8").read()
    report = json.loads(text)
    assert report["emotion"] == "angry" and report["probabilities"]["angry"] == 0.9 and len(report["probabilities"]) == 8
    assert "/secret/" not in text  # không lộ đường dẫn tệp trên máy chủ


def test_empty_state_values_have_one_slot_per_output():
    assert len(history._detail_empty()) == 7 and history._table_value([]) == history.EMPTY_TABLE


def test_fetch_requires_login():
    import gradio as gr

    with pytest.raises(gr.Error):
        history._fetch(1, 10, None, "", T.HISTORY_ALL_EMOTIONS, T.HISTORY_TIME_CHOICES[1])


def test_fetch_with_no_history_shows_empty_state(monkeypatch):
    monkeypatch.setattr(history.history_service, "list_history", lambda *a, **k: ([], 0))
    monkeypatch.setattr(history.history_service, "summarize_history", lambda *a, **k: {"total": 0, "avg_confidence": 0.0})
    monkeypatch.setattr(history.history_service, "export_history_csv", lambda *a, **k: "﻿")
    monkeypatch.setattr(history, "_export_dir", lambda: __import__("pathlib").Path(__import__("tempfile").gettempdir()))
    user = SessionUser(user_id=5, username="an", email="a@x.vn")
    total, outputs = history._fetch(1, 10, user, "", T.HISTORY_ALL_EMOTIONS, T.HISTORY_TIME_CHOICES[1])
    table, rows, _header, _head, empty_col, table_col, drawer = outputs[:7]
    assert total == 0 and rows == [] and table == history.EMPTY_TABLE
    assert empty_col["visible"] is True and table_col["visible"] is False and drawer["visible"] is False


def test_fetch_survives_database_failure(monkeypatch):
    def boom(*args, **kwargs):
        raise OperationalError("select", {}, Exception("db down"))

    monkeypatch.setattr(history.history_service, "list_history", boom)
    warned = []
    monkeypatch.setattr(history.gr, "Warning", lambda message: warned.append(message))
    user = SessionUser(user_id=5, username="an", email="a@x.vn")
    total, outputs = history._fetch(1, 10, user, "", T.HISTORY_ALL_EMOTIONS, T.HISTORY_TIME_CHOICES[1])
    assert total == 0 and outputs[1] == [] and warned == [T.MSG_DB_ERROR]  # báo lỗi kết nối thay vì làm sập trang
