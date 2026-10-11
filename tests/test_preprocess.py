# UC03/UC07 tiền xử lý (báo cáo Mục 3.1): 16 kHz mono, cắt lặng top_db=25, chuẩn hóa [-1,1], cố định 48.000 mẫu.
import pytest


@pytest.mark.skip(reason="TODO: port ml/preprocess.py từ ser_project/src/preprocess.py rồi kiểm tra đầu ra luôn có đúng 48.000 mẫu")
def test_output_is_exactly_48000_samples():
    ...


@pytest.mark.skip(reason="TODO: kiểm tra biên độ đầu ra nằm trong [-1, 1] và tệp toàn khoảng lặng không làm hàm lỗi")
def test_amplitude_normalized_and_silence_safe():
    ...
