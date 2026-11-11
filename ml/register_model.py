# Đăng ký một mô hình THẬT vào bảng models: nạp checkpoint, đánh giá trên tập kiểm thử, đo độ trễ, đếm tham số, đo dung lượng rồi ghi DB.
# Chạy lại với cùng --name để cập nhật số đo (ví dụ sau khi huấn luyện lại). Không có số nào được nhập tay.
#   python -m ml.register_model --checkpoint ml/weights/best_distilhubert_lora.pt --name "DistilHuBERT + LoRA" --type Transformer --activate
# Mô hình CREMA-D 6 nhãn (chỉ để so sánh, không đặt làm mô hình đang dùng):
#   python -m ml.register_model --labels cremad6 --checkpoint ml/weights/cremad6_distilhubert_lora.pt
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

from core.config import PROJECT_DIR, settings
from ml import benchmark, evaluate
from ml.config import LABEL_SETS
from ml.inference import build_model, pick_device

DEFAULT_DATASET_DESC = "RAVDESS Actor 22–24 (X_test của waveforms_cache.npz, độc lập người nói)"
CREMAD_DATASET_DESC = "CREMA-D 15 diễn viên test (cremad_test.npz, độc lập người nói)"
CREMAD_NAME = "DistilHuBERT + LoRA (CREMA-D, 6 nhãn)"
CREMAD_CHECKPOINT = "ml/weights/cremad6_distilhubert_lora.pt"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Đăng ký và đo mô hình DistilHuBERT + LoRA vào bảng models.")
    parser.add_argument("--labels", choices=sorted(LABEL_SETS), default="ravdess8", help="Bộ nhãn của mô hình: ravdess8 (mô hình chính) hoặc cremad6 (chỉ để so sánh)")
    parser.add_argument("--checkpoint", default=None, help="Tệp .pt (mặc định MODEL_CHECKPOINT_PATH; với cremad6 là ml/weights/cremad6_distilhubert_lora.pt)")
    parser.add_argument("--name", default=None, help="Tên hiển thị, duy nhất; trùng tên thì cập nhật")
    parser.add_argument("--type", dest="model_type", default="Transformer", help="Loại mô hình hiển thị (Cổ điển / Mạng sâu / Transformer)")
    parser.add_argument("--dataset", default=None, help="Tệp .npz tập kiểm thử (mặc định EVAL_DATASET_PATH; với cremad6 là EVAL_CREMAD_PATH)")
    parser.add_argument("--dataset-desc", default=None, help="Mô tả tập kiểm thử ghi vào DB")
    parser.add_argument("--repeats", type=int, default=30, help="Số lần chạy khi đo độ trễ")
    parser.add_argument("--activate", action="store_true", help="Đặt làm mô hình đang dùng")
    args = parser.parse_args(argv)

    compare_only = args.labels != "ravdess8"  # khác bộ nhãn của hệ thống: chỉ để so sánh, không suy luận trong ứng dụng
    if compare_only and args.activate:
        print("Mô hình khác bộ nhãn của hệ thống chỉ dùng để so sánh, không dùng --activate.", file=sys.stderr)
        return 1
    labels = LABEL_SETS[args.labels]
    if args.checkpoint is None:
        args.checkpoint = str(PROJECT_DIR / CREMAD_CHECKPOINT) if compare_only else str(settings.checkpoint_path)
    args.name = args.name or (CREMAD_NAME if compare_only else "DistilHuBERT + LoRA")
    args.dataset = args.dataset or str(settings.eval_cremad_file if compare_only else settings.eval_dataset_file)
    args.dataset_desc = args.dataset_desc or (CREMAD_DATASET_DESC if compare_only else DEFAULT_DATASET_DESC)

    checkpoint = Path(args.checkpoint).resolve()
    if not checkpoint.exists():
        print(f"Không thấy checkpoint: {checkpoint}", file=sys.stderr)
        return 1

    device = pick_device()
    print(f"[1/5] Nạp {checkpoint.name} lên {device} ...")
    model = build_model(checkpoint, device, num_classes=len(labels["names"]))

    print(f"[2/5] Đánh giá trên tập kiểm thử {args.dataset} ...")
    x, y = evaluate.load_eval_set(args.dataset)
    result = evaluate.evaluate_model(model, x, y, device, args.labels)

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
        **({"inference": False, "family": args.labels, "labels": labels["names"], "labels_vi": labels["names_vi"], "dataset_label": "CREMA-D"} if compare_only else {}),
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
