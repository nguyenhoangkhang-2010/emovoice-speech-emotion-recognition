# Ô chọn khoảng ngày (ui/components/daterange.py): chuỗi do lịch ghi vào ô -> (từ ngày, đến ngày) cho tầng dịch vụ.
import pytest

from ui.components import daterange
from ui.pages import admin_logs, history
from ui import i18n_vi as T


def test_parse_single_day_and_range_from_the_calendar_text():
    assert daterange.parse("16/10/2026") == ("2026-10-16", "2026-10-16")  # một ngày: hai đầu giống nhau
    assert daterange.parse("16/10/2026 – 20/10/2026") == ("2026-10-16", "2026-10-20")
    assert daterange.parse("  5/1/2026   –   7/1/2026 ") == ("2026-01-05", "2026-01-07")  # khoảng trắng thừa, ngày/tháng một chữ số


def test_parse_accepts_iso_dates_and_other_separators():
    assert daterange.parse("2026-10-16") == ("2026-10-16", "2026-10-16")  # dấu '-' trong ngày ISO không bị hiểu là dấu phân cách
    assert daterange.parse("2026-10-16 - 2026-10-20") == ("2026-10-16", "2026-10-20")
    assert daterange.parse("16/10/2026 đến 20/10/2026") == ("2026-10-16", "2026-10-20")


def test_parse_empty_means_no_date_filter():
    assert daterange.parse("") == (None, None) and daterange.parse(None) == (None, None) and daterange.parse("   ") == (None, None)


@pytest.mark.parametrize("text", ["hôm qua", "16-10-2026", "32/13/2026x", "16/10/2026 – 18/10/2026 – 20/10/2026", "16/10"])
def test_parse_rejects_garbage(text):
    with pytest.raises(ValueError, match="Khoảng ngày không hợp lệ"):
        daterange.parse(text)


def test_pages_turn_the_range_into_service_filters(monkeypatch):
    seen = {}

    def fake_list_logs(session, page, size, level, on_date, q, service, date_from, date_to):
        seen["logs"] = (date_from, date_to)
        return [], 0

    monkeypatch.setattr(admin_logs.admin_service, "list_logs", fake_list_logs)
    monkeypatch.setattr(admin_logs, "guard_admin", lambda session: None)
    admin_logs._fetch(None, 1, 10, T.LOG_LEVELS[0], T.LOG_ALL_SERVICES, "16/10/2026 – 20/10/2026", "")
    assert seen["logs"] == ("2026-10-16", "2026-10-20")
    admin_logs._fetch(None, 1, 10, T.LOG_LEVELS[0], T.LOG_ALL_SERVICES, "", "")
    assert seen["logs"] == (None, None)  # ô trống: không lọc theo ngày


def test_history_uses_the_range_only_in_custom_mode(monkeypatch):
    from core.session import SessionUser

    seen = []

    def fake_list(session, page, size, key, days, q, **span):
        seen.append(span)
        return [], 0

    monkeypatch.setattr(history.history_service, "list_history", fake_list)
    monkeypatch.setattr(history.history_service, "summarize_history", lambda *a, **k: {"avg_confidence": 0.0})
    monkeypatch.setattr(history.history_service, "export_history_csv", lambda *a, **k: "")
    user = SessionUser(user_id=5, username="u", email="u@x")
    history._fetch(1, 10, user, "", T.HISTORY_ALL_EMOTIONS, T.HISTORY_TIME_CUSTOM, "16/10/2026 – 20/10/2026")
    history._fetch(1, 10, user, "", T.HISTORY_ALL_EMOTIONS, T.HISTORY_TIME_CHOICES[1], "16/10/2026 – 20/10/2026")  # mục 30 ngày qua: bỏ qua ô lịch
    assert seen == [{"date_from": "2026-10-16", "date_to": "2026-10-20"}, {}]
