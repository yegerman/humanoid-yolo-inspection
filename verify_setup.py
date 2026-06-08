"""
Quick environment verification — run this before anything else.

Usage:
    python verify_setup.py
"""

import sys
import importlib

REQUIRED = [
    ("mujoco",      "3.1.0"),
    ("ultralytics", "8.0.0"),
    ("cv2",         "4.0.0"),
    ("numpy",       "1.24.0"),
    ("scipy",       "1.10.0"),
]

OPTIONAL = [
    ("dm_control", "1.0.0"),
    ("requests",   "2.28.0"),
]

def check_version(pkg_name: str, min_ver: str) -> tuple[bool, str]:
    try:
        mod = importlib.import_module(pkg_name)
        ver = getattr(mod, "__version__", "unknown")
        return True, ver
    except ImportError:
        return False, "NOT INSTALLED"

def main():
    print("=" * 55)
    print("  Humanoid Inspection POC — Environment Check")
    print("=" * 55)

    all_ok = True
    print("\nRequired packages:")
    for pkg, min_ver in REQUIRED:
        ok, ver = check_version(pkg, min_ver)
        status = "OK  " if ok else "FAIL"
        marker = "✓" if ok else "✗"
        print(f"  [{status}] {pkg:<20} {ver}")
        if not ok:
            all_ok = False

    print("\nOptional packages:")
    for pkg, min_ver in OPTIONAL:
        ok, ver = check_version(pkg, min_ver)
        status = "OK  " if ok else "warn"
        print(f"  [{status}] {pkg:<20} {ver}")

    print("\nMuJoCo scene files:")
    from pathlib import Path
    root = Path(__file__).parent
    scenes = [
        root / "scene" / "inspection_scene_standalone.xml",
        root / "scene" / "inspection_scene.xml",
    ]
    for s in scenes:
        exists = s.exists()
        print(f"  [{'OK  ' if exists else 'miss'}] {s.relative_to(root)}")

    print("\nTrained model:")
    best_pt   = root / "runs" / "train" / "weights" / "best.pt"
    best_onnx = root / "runs" / "train" / "weights" / "best.onnx"
    for m in [best_pt, best_onnx]:
        exists = m.exists()
        print(f"  [{'OK  ' if exists else 'miss'}] {m.relative_to(root)}")

    print("\nQuick MuJoCo load test (standalone scene):")
    standalone = root / "scene" / "inspection_scene_standalone.xml"
    if standalone.exists():
        try:
            import mujoco
            model = mujoco.MjModel.from_xml_path(str(standalone))
            data  = mujoco.MjData(model)
            mujoco.mj_forward(model, data)
            print(f"  [OK  ] Loaded — nq={model.nq}  nu={model.nu}  "
                  f"nbody={model.nbody}  ncam={model.ncam}")
        except Exception as e:
            print(f"  [FAIL] {e}")
            all_ok = False
    else:
        print("  [skip] Scene file missing")

    print("\n" + "=" * 55)
    if all_ok:
        print("  All checks passed. Ready for Day 1 Step 4.")
    else:
        print("  Some checks FAILED. Install missing packages:")
        print("    .venv\\Scripts\\activate")
        print("    pip install -r requirements.txt")
    print("=" * 55 + "\n")
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
