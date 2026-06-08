"""
Cosmos 3 augmentation via NVIDIA NIM API (image-to-image).
Sends synthetic MuJoCo frames and retrieves photorealistic industrial variants.

Usage:
    set NVIDIA_API_KEY=nvapi-xxxx
    python vision/augment_cosmos.py [--n 500] [--strength 0.6]

Free trial credits at: https://build.nvidia.com
"""

import argparse
import base64
import os
import random
import sys
import time
from pathlib import Path

import requests
from PIL import Image
import io

ROOT = Path(__file__).parent.parent
RAW_DIR  = ROOT / "data" / "images" / "train"
AUG_DIR  = ROOT / "data" / "augmented"
LBL_SRC  = ROOT / "data" / "labels" / "train"
LBL_DST  = ROOT / "data" / "labels" / "train"  # reuse same label (no bbox change)

NIM_URL = "https://ai.api.nvidia.com/v1/genai/nvidia/cosmos-1.0-diffusion"

INDUSTRIAL_PROMPTS = [
    "industrial factory floor, harsh fluorescent lighting, worn metal surfaces, photorealistic",
    "manufacturing plant, high contrast lighting, steel conveyor, photorealistic quality inspection",
    "factory workstation, cool overhead lights, scratched metal table, industrial realism",
    "assembly line inspection station, mixed daylight and fluorescent, aged metal, photorealistic",
]


def encode_image(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def cosmos_augment(api_key: str, image_path: Path, strength: float,
                   retries: int = 3) -> bytes | None:
    """Call Cosmos NIM API and return augmented image bytes, or None on failure."""
    b64 = encode_image(image_path)
    prompt = random.choice(INDUSTRIAL_PROMPTS)

    payload = {
        "image":    b64,
        "prompt":   prompt,
        "strength": strength,
        "num_inference_steps": 30,
        "guidance_scale": 7.5,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }

    for attempt in range(retries):
        try:
            resp = requests.post(NIM_URL, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                result = resp.json()
                # NIM returns base64-encoded image in result["output"] or result["image"]
                img_b64 = result.get("output") or result.get("image") or result.get("artifacts", [{}])[0].get("base64")
                if img_b64:
                    return base64.b64decode(img_b64)
                print(f"  Warning: unexpected response shape: {list(result.keys())}")
                return None
            elif resp.status_code == 429:
                wait = 2 ** attempt
                print(f"  Rate limited, waiting {wait}s …")
                time.sleep(wait)
            else:
                print(f"  API error {resp.status_code}: {resp.text[:200]}")
                return None
        except requests.RequestException as e:
            print(f"  Request failed (attempt {attempt+1}): {e}")
            time.sleep(2)

    return None


def augment_dataset(api_key: str, n: int, strength: float):
    AUG_DIR.mkdir(parents=True, exist_ok=True)

    all_images = sorted(RAW_DIR.glob("*.jpg"))
    if not all_images:
        sys.exit(f"No images found in {RAW_DIR}. Run generate_data.py first.")

    sample = random.sample(all_images, min(n, len(all_images)))
    print(f"Augmenting {len(sample)} images via Cosmos NIM …")

    ok, fail = 0, 0
    for i, img_path in enumerate(sample):
        aug_path = AUG_DIR / f"aug_{img_path.name}"
        if aug_path.exists():
            ok += 1
            continue

        img_bytes = cosmos_augment(api_key, img_path, strength)

        if img_bytes:
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            img.save(str(aug_path), "JPEG", quality=92)

            # Copy label file (bounding box unchanged — only texture changed)
            lbl_src = LBL_SRC / f"{img_path.stem}.txt"
            lbl_dst = AUG_DIR.parent / "labels" / "train" / f"aug_{img_path.stem}.txt"
            if lbl_src.exists():
                lbl_dst.parent.mkdir(parents=True, exist_ok=True)
                lbl_dst.write_text(lbl_src.read_text())

            ok += 1
        else:
            fail += 1

        if (i + 1) % 25 == 0:
            print(f"  {i+1}/{len(sample)}  ok={ok}  fail={fail}")

        # Polite rate limiting: ~1 req/s
        time.sleep(0.8)

    print(f"\nAugmentation complete. ok={ok}  fail={fail}")
    print(f"Augmented images saved to {AUG_DIR}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=500)
    parser.add_argument("--strength", type=float, default=0.6,
                        help="Diffusion strength 0–1 (higher = more change)")
    args = parser.parse_args()

    api_key = os.environ.get("NVIDIA_API_KEY", "")
    if not api_key:
        sys.exit(
            "Set NVIDIA_API_KEY env var.\n"
            "Get free trial credits at https://build.nvidia.com"
        )

    augment_dataset(api_key, args.n, args.strength)


if __name__ == "__main__":
    main()
