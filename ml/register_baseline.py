# Đăng ký baseline cổ điển (Random Forest) vào bảng models để SO SÁNH với mô hình chính trên trang Mô hình & hiệu năng.
# Baseline không có attention nên không dùng để suy luận / XAI: được ghi với inference=false và không đặt làm mô hình đang dùng.
#   python -m ml.register_baseline --checkpoint <final_rf_baseline.pkl> --name "Random Forest"
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core.config import settings
from ml import benchmark, evaluate

DEFAULT_DATASET_DESC = "RAVDESS Actor 22–24 (X_test của features_212_cache.npz, độc lập người nói)"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Đăng ký và đo mô hình Random Forest baseline vào bảng models.")
    parser.add_argument("--checkpoint", required=True, help="Tệp .pkl của scikit-learn (chỉ nạp tệp do nhóm huấn luyện tạo: pickle có thể chạy mã)")
    parser.add_argument("--name", default="Random Forest", help="Tên hiển thị, duy nhất; trùng tên thì cập nhật")
    parser.add_argument("--type", dest="model_type", default="Cổ điển", help="Loại mô hình hiển thị")
    parser.add_argument("--features", default=str(settings.eval_features_file), help="Tệp .npz có X_test (N x 212), y_test")
    parser.add_argument("--dataset-desc", default=DEFAULT_DATASET_DESC, help="Mô tả tập kiểm thử ghi vào DB")
    parser.add_argument("--repeats", type=int, default=200, help="Số lần chạy khi đo độ trễ")
    args = parser.parse_args(argv)

    checkpoint = Path(args.checkpoint).resolve()
    if not checkpoint.exists():
        print(f"Không thấy checkpoint: {checkpoint}", file=sys.stderr)
        return 1

    import joblib

    print(f"[1/4] Nạp {checkpoint.name} ...")
    model = joblib.load(checkpoint)
    if getattr(model, "n_features_in_", 212) != 212:
        print(f"Mô hình nhận {model.n_features_in_} đặc trưng, cần 212.", file=sys.stderr)
        return 1

    print(f"[2/4] Đánh giá trên {args.features} ...")
    x, y = evaluate.load_eval_features(args.features)
    result = evaluate.summarize(y, model.predict(x))

    print("[3/4] Đo dung lượng và độ trễ (chỉ bước predict, chưa tính trích 212 đặc trưng) ...")
    size_mib = benchmark.checkpoint_size_mib(checkpoint)
    if hasattr(model, "n_jobs"):
        model.n_jobs = 1  # một mẫu mỗi lần: song song hóa theo cây chỉ thêm chi phí khởi tạo luồng
    latency = benchmark.measure_latency_ms(lambda sample: model.predict(sample), x[:1], repeats=args.repeats)

    print("[4/4] Ghi vào bảng models ...")
    from services import model_service

    params = {k: v for k, v in model.get_params().items() if k in ("n_estimators", "max_depth", "min_samples_split", "class_weight")}
    details = {
        "inference": False,
        "family": "random_forest",
        "hyperparameters": params,
        "macro_precision": result["macro_precision"],
        "macro_recall": result["macro_recall"],
        "per_class": result["per_class"],
        "confusion": result["confusion"],
        "latency": {"batch_size": 1, "repeats": args.repeats, "device": "cpu", "scope": "predict, n_jobs=1, không gồm trích đặc trưng"},
    }
    saved = model_service.register_model(
        name=args.name,
        model_type=args.model_type,
        checkpoint_path=str(checkpoint),
        accuracy=result["accuracy"],
        f1_score=result["macro_f1"],
        size_mb=size_mib,
        inference_time=latency,
        params_total=None,
        params_trainable=None,
        eval_dataset=args.dataset_desc,
        eval_samples=len(y),
        latency_device="cpu",
        details=details,
    )
    print(f"Xong: {saved['name']} | accuracy {saved['accuracy']}% | F1 {saved['macro_f1']}% | {saved['size_mib']} MiB | {saved['latency_ms']} ms/mẫu (cpu) | baseline: chỉ để so sánh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
