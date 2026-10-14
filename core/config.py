# Cấu hình đọc từ .env ở thư mục gốc emovoice/ (python-dotenv); dùng chung toàn ứng dụng.
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv chưa cài: dùng biến môi trường hệ thống
    load_dotenv = None

PROJECT_DIR = Path(__file__).resolve().parents[1]
if load_dotenv is not None:
    load_dotenv(PROJECT_DIR / ".env")


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _flag(name: str) -> bool:
    return _env(name, "0").strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    database_url: str = field(default_factory=lambda: _env("DATABASE_URL", "sqlite:///./emovoice.db"))
    secret_key: str = field(default_factory=lambda: _env("SECRET_KEY", "change-me"))
    max_upload_mb: int = field(default_factory=lambda: int(_env("MAX_UPLOAD_MB", "10")))
    allowed_audio: str = field(default_factory=lambda: _env("ALLOWED_AUDIO", "wav,mp3"))
    low_confidence_threshold: float = field(default_factory=lambda: float(_env("LOW_CONFIDENCE_THRESHOLD", "0.30")))
    eval_dataset_path: str = field(default_factory=lambda: _env("EVAL_DATASET_PATH", "data/waveforms_cache.npz"))
    model_checkpoint_path: str = field(default_factory=lambda: _env("MODEL_CHECKPOINT_PATH", "ml/weights/best_distilhubert_lora.pt"))
    password_reset_ttl_minutes: int = field(default_factory=lambda: int(_env("PASSWORD_RESET_TTL_MINUTES", "15")))
    server_port: int = field(default_factory=lambda: int(_env("SERVER_PORT", "7860")))
    dev_bypass_login: bool = field(default_factory=lambda: _flag("DEV_BYPASS_LOGIN"))
    enable_admin_extra_pages: bool = field(default_factory=lambda: _flag("ENABLE_ADMIN_EXTRA_PAGES"))
    admin_username: str = field(default_factory=lambda: _env("ADMIN_USERNAME", "admin"))
    admin_email: str = field(default_factory=lambda: _env("ADMIN_EMAIL", "admin@emovoice.local"))
    admin_password: str = field(default_factory=lambda: _env("ADMIN_PASSWORD", "change-me-admin"))

    @property
    def allowed_audio_list(self) -> List[str]:
        return [ext.strip().lower() for ext in self.allowed_audio.split(",") if ext.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def checkpoint_path(self) -> Path:
        path = Path(self.model_checkpoint_path)
        return path if path.is_absolute() else PROJECT_DIR / path

    @property
    def eval_dataset_file(self) -> Path:
        """Tệp .npz có X_test (N x 48000), y_test: tập kiểm thử độc lập dùng khi đăng ký / đánh giá mô hình."""
        path = Path(self.eval_dataset_path)
        return path if path.is_absolute() else PROJECT_DIR / path

    @property
    def upload_dir(self) -> Path:
        return PROJECT_DIR / "storage" / "uploads"

    @property
    def heatmap_dir(self) -> Path:
        return PROJECT_DIR / "storage" / "heatmaps"

    @property
    def mel_dir(self) -> Path:
        return PROJECT_DIR / "storage" / "mel"

    @property
    def log_dir(self) -> Path:
        return PROJECT_DIR / "logs"


settings = Settings()
