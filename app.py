# Điểm vào duy nhất của EmoVoice (Gradio): python app.py. Cấu hình lấy từ .env (xem .env.example).
from core.config import settings
from ui import theme
from ui.layout import build_app

demo = build_app()  # Hugging Face Spaces / Colab có thể import `demo`

if __name__ == "__main__":
    _, launch_kwargs = theme.app_kwargs()  # gradio 6: theme/css/head truyền ở launch(); gradio 5: đã truyền ở gr.Blocks()
    demo.queue()
    demo.launch(server_port=settings.server_port, allowed_paths=[str(settings.upload_dir), str(settings.heatmap_dir), str(settings.mel_dir)], **launch_kwargs)
