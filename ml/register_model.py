# Đăng ký một mô hình THẬT vào bảng models: nạp checkpoint, đánh giá trên tập kiểm thử, đo độ trễ, đếm tham số, đo dung lượng rồi ghi DB.
# Chạy lại với cùng --name để cập nhật số đo (ví dụ sau khi huấn luyện lại). Không có số nào được nhập tay.
#   python -m ml.register_model --checkpoint ml/weights/best_distilhubert_lora.pt --name "DistilHuBERT + LoRA" --type Transformer --activate
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

from core.config import settings
from ml import benchmark, evaluate
from ml.inference import build_model, pick_device

DEFAULT_DATASET_DESC = "RAVDESS Actor 22–24 (X_test của waveforms_cache.npz, độc lập người nói)"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Đăng ký và đo mô hình DistilHuBERT + LoRA vào bảng models.")
    parser.add_argument("--checkpoint", default=str(settings.checkpoint_path), help="Tệp state_dict .pt (mặc định MODEL_CHECKPOINT_PATH)")
    parser.add_argument("--name", default="DistilHuBERT + LoRA", help="Tên hiển thị, duy nhất; trùng tên thì cập nhật")
    parser.add_argument("--type", dest="model_type", default="Transformer", help="Loại mô hình hiển thị (Cổ điển / Mạng sâu / Transformer)")
    parser.add_argument("--dataset", default=str(settings.eval_dataset_file), help="Tệp .npz có X_test, y_test (mặc định EVAL_DATASET_PATH)")
    parser.add_argument("--dataset-desc", default=DEFAULT_DATASET_DESC, help="Mô tả tập kiểm thử ghi vào DB")
    parser.add_argument("--repeats", type=int, default=30, help="Số lần chạy khi đo độ trễ")
    parser.add_argument("--activate", action="store_true", help="Đặt làm mô hình đang dùng")
    args = parser.parse_args(argv)

    checkpoint = Path(args.checkpoint).resolve()
    if not checkpoint.exists():
        print(f"Không thấy checkpoint: {checkpoint}", file=sys.stderr)
        return 1

    device = pick_device()
    print(f"[1/5] Nạp {checkpoint.name} lên {device} ...")
    model = build_model(checkpoint, device)

    print(f"[2/5] Đánh giá trên tập kiểm thử {args.dataset} ...")
    x, y = evaluate.load_eval_set(args.dataset)
    result = evaluate.evaluate_model(model, x, y, device)

    print("[3/5] Đếm tham số và đo dung lượng ...")
    params = benchmark.count_parameters(model)
    size_mib = benchmark.checkpoint_size_mib(checkpoint)

    print(f"[4/5] Đo độ trễ (batch 1, {args.repeats} lần, có khởi động trước) ...")

    def predict_one(sample):
        with torch.no_grad():
            model(torch.from_numpy(sample).unsqueeze(0).to(device))

    sync = torch.cuda.synchronize if device.type == "cuda" else (lambda: None)
    latency = benchmark.measure_latency_ms(predict_one, x[0], repeats=args.repeats, sync=sync)

    print("[5/5] Ghi vào bảng models ...")
    from services import model_service

    details = {
        "macro_precision": result["macro_precision"],
        "macro_recall": result["macro_recall"],
        "per_class": result["per_class"],
        "confusion": result["confusion"],
        "latency": {"batch_size": 1, "repeats": args.repeats, "device": device.type},
        "torch_version": torch.__version__,
    }
    saved = model_service.register_model(
        name=args.name,
        model_type=args.model_type,
        checkpoint_path=str(checkpoint),
        accuracy=result["accuracy"],
        f1_score=result["macro_f1"],
        size_mb=size_mib,
        inference_time=latency,
        params_total=params["total"],
        params_trainable=params["trainable"],
        eval_dataset=args.dataset_desc,
        eval_samples=len(y),
        latency_device=device.type,
        details=details,
        activate=args.activate,
    )
    print(
        f"Xong: {saved['name']} | accuracy {saved['accuracy']}% | F1 {saved['macro_f1']}% | {saved['size_mib']} MiB | "
        f"{saved['latency_ms']} ms/mẫu ({device.type}) | tham số {saved['params_trainable']:,}/{saved['params_total']:,} | "
        f"{'ĐANG DÙNG' if saved['status'] == 'active' else 'chưa kích hoạt'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
