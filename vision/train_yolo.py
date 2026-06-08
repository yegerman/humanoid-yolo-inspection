"""
Fine-tune YOLOv8n on synthetic inspection data (CPU mode for AMD GPU).

Usage:
    python vision/train_yolo.py [--epochs 50] [--batch 8] [--imgsz 480]

After training, model saved to runs/train/weights/best.onnx
"""

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

def check_dataset(data_yaml: Path):
    train_dir = ROOT / "data" / "images" / "train"
    val_dir   = ROOT / "data" / "images" / "val"

    n_train = len(list(train_dir.glob("*.jpg"))) if train_dir.exists() else 0
    n_val   = len(list(val_dir.glob("*.jpg")))   if val_dir.exists()   else 0

    if n_train == 0:
        sys.exit(
            f"No training images found in {train_dir}.\n"
            "Run: python vision/generate_data.py"
        )
    print(f"Dataset: {n_train} train / {n_val} val images")
    return n_train, n_val


def merge_augmented(aug_dir: Path):
    """Copy Cosmos-augmented images+labels into the training split."""
    aug_imgs = list(aug_dir.glob("*.jpg"))
    if not aug_imgs:
        return

    dst_img = ROOT / "data" / "images" / "train"
    dst_lbl = ROOT / "data" / "labels" / "train"
    lbl_src  = ROOT / "data" / "labels" / "train"

    copied = 0
    for p in aug_imgs:
        shutil.copy2(p, dst_img / p.name)
        lbl = aug_dir.parent / "labels" / "train" / f"{p.stem}.txt"
        if not lbl.exists():
            # try original label name (strip "aug_" prefix)
            orig_stem = p.stem.removeprefix("aug_")
            lbl = lbl_src / f"{orig_stem}.txt"
        if lbl.exists():
            shutil.copy2(lbl, dst_lbl / f"{p.stem}.txt")
        copied += 1

    print(f"Merged {copied} augmented images into training set")


def train(epochs: int, batch: int, imgsz: int, workers: int):
    from ultralytics import YOLO

    data_yaml = ROOT / "data" / "dataset.yaml"
    check_dataset(data_yaml)

    aug_dir = ROOT / "data" / "augmented"
    if aug_dir.exists() and any(aug_dir.glob("*.jpg")):
        merge_augmented(aug_dir)

    model = YOLO("yolov8n.pt")

    results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device="cpu",
        workers=workers,
        project=str(ROOT / "runs"),
        name="train",
        exist_ok=True,
        patience=15,
        cache=False,       # avoid OOM on 16GB
        amp=False,         # CPU: no mixed precision
        verbose=True,
    )

    best_pt   = ROOT / "runs" / "train" / "weights" / "best.pt"
    best_onnx = ROOT / "runs" / "train" / "weights" / "best.onnx"

    if best_pt.exists():
        print(f"\nBest checkpoint: {best_pt}")
        # Export to ONNX for faster CPU inference
        export_model = YOLO(str(best_pt))
        export_model.export(format="onnx", imgsz=imgsz, simplify=True)
        print(f"ONNX model: {best_onnx}")
    else:
        print("Training complete (best.pt not found — check runs/train/)")

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs",  type=int, default=50)
    parser.add_argument("--batch",   type=int, default=8,
                        help="Reduce to 4 if RAM pressure occurs")
    parser.add_argument("--imgsz",   type=int, default=480)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()

    print(f"Training YOLOv8n  epochs={args.epochs}  batch={args.batch}  "
          f"imgsz={args.imgsz}  device=cpu")
    train(args.epochs, args.batch, args.imgsz, args.workers)


if __name__ == "__main__":
    main()
