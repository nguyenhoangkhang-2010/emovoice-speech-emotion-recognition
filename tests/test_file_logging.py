# Nhật ký ra tệp (feat/file-logging): core.logging.setup_logging ghi logs/emovoice.log, không nhân đôi, không làm hỏng ứng dụng khi không ghi được tệp.
import logging

import pytest

from core import logging as app_logging


@pytest.fixture(autouse=True)
def restore_root_logger():
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    yield
    for h in list(root.handlers):
        if h not in handlers:
            root.removeHandler(h)
            h.close()
    root.setLevel(level)


def _flush():
    for h in logging.getLogger().handlers:
        h.flush()


def test_setup_writes_records_to_the_log_file(tmp_path):
    path = app_logging.setup_logging(tmp_path / "logs")
    assert path == tmp_path / "logs" / "emovoice.log"  # thư mục chưa có thì được tạo
    logging.getLogger("services.demo").warning("tệp %s bị từ chối", "a.wav")
    try:
        raise ValueError("hỏng")
    except ValueError:
        logging.getLogger("services.demo").exception("không xử lý được")
    _flush()
    text = path.read_text(encoding="utf-8")
    assert "WARNING" in text and "services.demo: tệp a.wav bị từ chối" in text
    assert "Traceback" in text and "ValueError: hỏng" in text  # traceback chỉ có trong tệp, không có trong system_logs


def test_calling_setup_twice_does_not_duplicate_lines(tmp_path):
    app_logging.setup_logging(tmp_path)
    path = app_logging.setup_logging(tmp_path)
    logging.getLogger("x").warning("một lần")
    _flush()
    assert path.read_text(encoding="utf-8").count("một lần") == 1


def test_third_party_chatter_is_quiet_but_app_info_is_kept(tmp_path):
    path = app_logging.setup_logging(tmp_path)
    logging.getLogger("httpx").info("GET https://example")
    logging.getLogger("services.demo").info("nạp mô hình xong")
    _flush()
    text = path.read_text(encoding="utf-8")
    assert "nạp mô hình xong" in text and "GET https://example" not in text


def test_unwritable_log_dir_falls_back_to_console(tmp_path):
    blocker = tmp_path / "logs"
    blocker.write_text("day la tep, khong phai thu muc")  # mkdir trên đường dẫn này sẽ lỗi
    assert app_logging.setup_logging(blocker) is None  # không ném lỗi: ứng dụng vẫn khởi động
    logging.getLogger("x").warning("vẫn chạy")  # không hỏng khi chỉ còn console
