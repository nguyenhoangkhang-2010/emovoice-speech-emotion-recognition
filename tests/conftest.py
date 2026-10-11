# Cho phép `import core, services, ml, ui` khi chạy `python -m pytest tests` từ thư mục emovoice/.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
