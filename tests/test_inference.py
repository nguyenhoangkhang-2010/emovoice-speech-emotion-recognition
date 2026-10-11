# UC04 suy luận (báo cáo Bảng 2.6; yêu cầu phi chức năng: tiền xử lý + suy luận < 1,5 s cho đoạn 3 s; cảnh báo khi mọi xác suất < 30%).
import pytest


@pytest.mark.skip(reason="TODO: sau khi port ml/model.py + ml/inference.py, kiểm tra predict trả probs [8] có tổng = 1 và attn_weights [149]")
def test_predict_shapes_and_probabilities():
    ...


@pytest.mark.skip(reason="TODO: inference_service.is_low_confidence trả True khi max(probs) < 0,30 (LOW_CONFIDENCE_THRESHOLD)")
def test_low_confidence_flag():
    ...
