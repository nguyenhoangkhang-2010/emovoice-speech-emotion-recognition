# UC04 suy luận (báo cáo Bảng 2.6; yêu cầu phi chức năng: tiền xử lý + suy luận < 1,5 s cho đoạn 3 s; cảnh báo khi mọi xác suất < 30%).
import numpy as np
import pytest

from ml import xai
from services import inference_service as svc


def test_low_confidence_flag():
    assert svc.is_low_confidence(np.full(8, 0.125)) is True
    assert svc.is_low_confidence(np.array([0.29, 0.28, 0.2, 0.1, 0.05, 0.04, 0.02, 0.02])) is True
    assert svc.is_low_confidence(np.array([0.5, 0.2, 0.1, 0.1, 0.05, 0.02, 0.02, 0.01])) is False
    assert svc.is_low_confidence(np.array([0.4, 0.6]), threshold=0.7) is True


def test_resolve_checkpoint_prefers_active_model(monkeypatch, tmp_path):
    ckpt = tmp_path / "a.pt"
    ckpt.write_bytes(b"x")
    monkeypatch.setattr(svc.model_service, "active_model", lambda: {"name": "A", "key": "7", "checkpoint_path": str(ckpt)})
    assert svc._resolve_checkpoint() == ("A", str(ckpt), "7")


def test_resolve_checkpoint_reports_missing_file(monkeypatch, tmp_path):
    monkeypatch.setattr(svc.model_service, "active_model", lambda: {"name": "A", "checkpoint_path": str(tmp_path / "mat.pt")})
    with pytest.raises(svc.ModelNotReady, match="checkpoint"):
        svc._resolve_checkpoint()


def test_resolve_checkpoint_without_any_model(monkeypatch, tmp_path):
    monkeypatch.setattr(svc.model_service, "active_model", lambda: None)
    monkeypatch.setattr(svc.settings.__class__, "checkpoint_path", property(lambda self: tmp_path / "khong-co.pt"))
    with pytest.raises(svc.ModelNotReady, match="register_model"):
        svc._resolve_checkpoint()


def test_registry_down_falls_back_to_env_checkpoint(monkeypatch, tmp_path):
    ckpt = tmp_path / "env.pt"
    ckpt.write_bytes(b"x")

    def broken():
        raise svc.model_service.RegistryUnavailable("db down")

    monkeypatch.setattr(svc.model_service, "active_model", broken)
    monkeypatch.setattr(svc.settings.__class__, "checkpoint_path", property(lambda self: ckpt))
    assert svc._resolve_checkpoint() == ("env", str(ckpt), None)


def test_predict_rejects_wrong_length():
    pytest.importorskip("torch")
    from ml import inference

    with pytest.raises(ValueError):
        inference.predict(np.zeros(100, dtype=np.float32))


def test_attention_levels_are_discrete_and_cover_the_peak():
    attn = np.full(149, 0.001)
    attn[60:75] = 0.05  # đỉnh chú ý quanh 1,2–1,5 s
    levels = xai.attention_to_levels(attn)
    assert len(levels) == 30 and set(levels) <= set(range(5))
    assert max(levels) == 4 and levels[0] == 0
    lo, hi = xai.peak_range(levels)
    assert 1.0 <= lo < hi <= 1.6


def test_attention_levels_handle_degenerate_input():
    assert xai.attention_to_levels(np.zeros(149)) == [0] * 30
    assert xai.peak_range([]) == (0.0, 3.0)


def test_waveform_envelope_is_normalized():
    wave = np.concatenate([np.zeros(24000), np.sin(np.linspace(0, 200, 24000))]).astype(np.float32)
    env = xai.waveform_envelope(wave, 60)
    assert len(env) == 60 and max(env) == pytest.approx(1.0) and env[0] == 0.0
    assert xai.waveform_envelope(np.zeros(100), 10) == [0.0] * 10
