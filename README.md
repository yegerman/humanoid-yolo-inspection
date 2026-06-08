# Humanoid Robot Industrial Inspection POC

**Unitree G1 · MuJoCo 3.x · YOLOv8n · Cosmos 3 NIM API**

A 2-day proof-of-concept demonstrating a humanoid robot performing autonomous visual quality inspection at a simulated industrial work table. The G1's head camera detects defective parts and the robot arm removes them to a reject bin — all in simulation, on a Windows PC with an AMD GPU.

---

## 🚀 POC v2 — Gemini-Brain Inspection (current direction)

v2 upgrades the demo to the **two-layer architecture used by leading humanoids** (Google Gemini Robotics, Figure Helix, NVIDIA GR00T, Physical Intelligence π0): a **hosted VLM brain** that reasons over the scene + a **separate action layer** that moves the arm. You type an instruction in plain English — *"throw all the defective parts into the reject bin"* — and the robot does it in MuJoCo, **with no retraining**.

> **Status:** architecture + docs complete (this pass). Code build (`robosuite_demo.py`, `brains/`, `action/`) is the next approved pass.

**Design docs:** [`docs/Architecture_Design_Document_v2.docx`](docs/Architecture_Design_Document_v2.docx) · [`docs/PRD_v2.docx`](docs/PRD_v2.docx) · diagram: [`output/architecture_v2_diagram.png`](output/architecture_v2_diagram.png)

### What changes from v1

| | v1 (baseline, below) | v2 (this direction) |
|---|---|---|
| Brain | YOLOv8n (trained 2h on CPU) | **Gemini 2.0 Flash** — hosted, zero-shot |
| Decide | Hardcoded 5-state FSM | VLM reasoning → typed `Decision` (+ plain-English *why*) |
| Move arm | Keyframe poses | **robosuite OSC** (reliable) + optional Octo/GR00T VLA |
| Scene | Placeholder capsule | **robosuite `PickPlace`** BinsArena |
| Change behaviour | Edit code + retrain | **Edit one English sentence** |

### Mode matrix (planned CLI)

| Flag | Options | Default | Notes |
|------|---------|---------|-------|
| `--brain` | `gemini` · `groot` · `yolo` | `gemini` | hosted brain; `yolo` reuses v1 detector |
| `--action` | `scripted` · `octo` · `groot` | `scripted` | `scripted` = reliable; others = showcase |
| `--instruction` | free text | "throw all the defective parts into the reject bin" | the rule, in English |
| `--no-viewer` | flag | off | headless: saves annotated frames + metrics |

**Reliable, always-demoable path:** `--brain gemini --action scripted`.

### v2 setup + run (after the build pass)

```powershell
cd C:\huminoid
.venv\Scripts\activate
pip install robosuite google-generativeai

$env:GEMINI_API_KEY = "AIza..."          # free at aistudio.google.com
$env:NVIDIA_API_KEY = "nvapi-..."        # only for GR00T modes (already set)

python robosuite_demo.py --brain gemini --action scripted ^
        --instruction "throw all the defective parts into the reject bin"

# optional showcase (real generalist VLA drives the arm; expect jitter)
pip install -r requirements-octo.txt
python robosuite_demo.py --brain gemini --action octo
```

### Honest reality checks (documented in full in the Architecture doc)
- **Octo** zero-shot grasps are jittery without fine-tuning → showcase only; scripted OSC is the reliable backbone.
- **GR00T** is primarily open weights on HuggingFace, not guaranteed to be a hosted API → the build pass verifies an endpoint and degrades to Gemini-only if absent.
- **GR00T is a VLA action model**, slotted beside Octo — *not* a Gemini replacement. Gemini stays the decision brain.

---

## POC v1 — YOLOv8 baseline (below)

The original 2-day pipeline. Still intact and runnable; reused by v2's `--brain yolo` comparison mode.

## Quick Start

```powershell
cd C:\huminoid
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python verify_setup.py                         # sanity check
python vision\generate_data.py --n 2000        # ~5 min
python vision\train_yolo.py --epochs 50        # ~1.5 h on CPU
python demo.py --scene standalone              # runs the demo
```

---

## Hardware Requirements

| Component | Minimum | This POC |
|-----------|---------|---------|
| CPU | 4-core 3 GHz | i7-6700 3.4 GHz |
| RAM | 8 GB | 16 GB |
| GPU | OpenGL (any) | AMD RX 580 8 GB |
| Storage | 3 GB free | C:\ (E:\ is full) |
| OS | Windows 10 64-bit | Windows 10 Pro |

> No NVIDIA GPU required. Cosmos 3 augmentation uses the NVIDIA NIM cloud API (HTTP only).

---

## Project Structure

```
C:\huminoid\
├── scene\
│   ├── inspection_scene_standalone.xml   ← use this first (no G1 MJCF needed)
│   └── inspection_scene.xml              ← full scene (requires unitree_mujoco)
├── data\
│   ├── dataset.yaml
│   ├── images\{train,val}\
│   ├── labels\{train,val}\
│   └── augmented\
├── vision\
│   ├── generate_data.py      generate 2,000 labeled synthetic frames
│   ├── augment_cosmos.py     optional Cosmos 3 NIM augmentation
│   ├── train_yolo.py         fine-tune YOLOv8n (CPU mode)
│   └── detector.py           live detection class used by demo
├── robot\
│   ├── ik_solver.py          DLS IK + keyframe fallback for G1 right arm
│   └── inspection_controller.py   5-state FSM
├── demo.py                   main entry — viewer + control loop
├── verify_setup.py           pre-flight environment check
└── requirements.txt
```

---

## Pipeline

```
generate_data.py          train_yolo.py          demo.py
   │                           │                     │
   ▼                           ▼                     ▼
MuJoCo offscreen         YOLOv8n fine-tune      MuJoCo viewer
renderer (2,000           50 epochs, CPU        + OpenCV cam
frames + YOLO            → best.onnx             + controller
labels)                                           → arm moves
        │
        ▼  (optional)
  augment_cosmos.py
  NVIDIA NIM API
  +500 photorealistic
  variants
```

---

## Day-by-Day Plan

### Day 1

| Step | Command | Time |
|------|---------|------|
| 1. Install deps | `pip install -r requirements.txt` | 15 min |
| 2. Verify | `python verify_setup.py` | 2 min |
| 3. Get G1 MJCF | `git clone https://github.com/unitreerobotics/unitree_mujoco C:\unitree_mujoco` | 10 min |
| 4. Generate data | `python vision\generate_data.py --n 2000` | 5 min |
| 4b. Cosmos augment | `python vision\augment_cosmos.py --n 500` | 1 h (optional) |
| 5. Train | `python vision\train_yolo.py --epochs 50` | ~1.5 h |

### Day 2

| Step | Command | Time |
|------|---------|------|
| 6. Test standalone demo | `python demo.py --scene standalone` | instant |
| 7. Test full G1 scene | `python demo.py --scene full` | instant |
| 8. Record | Windows Game Bar `Win+G` | 10 min |

---

## Architecture

Four layers:

```
┌─────────────────────────────────────────────────────────┐
│  SIMULATION CORE   MuJoCo 3.9 · scene XML · G1 MJCF     │
├─────────────────────────────────────────────────────────┤
│  CONTROL LAYER     InspectionController · IKSolver       │
│                    5-state FSM: WATCH→PICK→DROP          │
├─────────────────────────────────────────────────────────┤
│  VISION PIPELINE   YOLOv8n (ONNX, CPU) · OpenCV HUD     │
│                    3 classes · ~80 ms/frame              │
├─────────────────────────────────────────────────────────┤
│  DATA / TRAINING   generate_data.py → train_yolo.py      │
│                    + Cosmos 3 NIM API (optional)         │
└─────────────────────────────────────────────────────────┘
```

See [Architecture_Design_Document.docx](Architecture_Design_Document.docx) for the full block diagram.

---

## Demo Scene: What You'll See

- **MuJoCo viewer** — 3D interactive view of the robot and table
- **OpenCV window** — annotated head-camera feed with bounding boxes
- **Console** — state transitions and 30-second metric summaries

Parts spawn every 5 seconds cycling through:
- **Green box** → `good` → arm stays home
- **Red box** → `defect_crack` → arm reaches, picks, drops in bin
- **Dark grey box** → `defect_discolor` → arm reaches, picks, drops in bin

---

## Cosmos 3 Augmentation (Optional)

```powershell
$env:NVIDIA_API_KEY = "nvapi-xxxx"   # from build.nvidia.com (free trial)
python vision\augment_cosmos.py --n 500 --strength 0.6
```

Sends synthetic frames to the NVIDIA NIM API and gets back photorealistic
industrial variants (factory floor textures, harsh fluorescent lighting).
Bounding box labels are preserved unchanged. Estimated cost: ~$0.01–0.05/image.

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Defect detection mAP | > 80% |
| False positive rate | < 20% |
| Arm reach success | > 70% of detections |
| Inference latency | < 150 ms/frame |
| Demo stability | 5 min without crash |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `XML root element not found` | Check scene XML doesn't start with `<![CDATA[` |
| `Schema violation: unrecognized attribute: 'site'` on camera | Use `pos=` + `euler=` on `<camera>` directly (MuJoCo 3.x) |
| YOLOv8 OOM during training | Set `--batch 4` and `cache=False` in train_yolo.py |
| `FileNotFoundError: No trained model` | Run `python vision\train_yolo.py` first |
| Arm doesn't move | Check detector found model; look for `[DETECT]` in console |
| MuJoCo path error | Keep project at `C:\huminoid` — short path required on Windows |

---

## Future Upgrade Path

1. **Real G1 MJCF** — clone `unitree_mujoco`, run `demo.py --scene full`
2. **Isaac Sim port** — same logic, photorealistic rendering (requires NVIDIA GPU)
3. **Cosmos 3 local** — run 16B model locally once NVIDIA GPU is available
4. **Real robot** — transfer `best.onnx` weights + IK controller to physical G1

---

## Documents

| Document | Description |
|----------|-------------|
| [docs/Architecture_Design_Document_v2.docx](docs/Architecture_Design_Document_v2.docx) | **v2** — Gemini-brain + action-layer architecture, industry landscape, MuJoCo demo path |
| [docs/PRD_v2.docx](docs/PRD_v2.docx) | **v2** — natural-language inspection requirements, success criteria, risks |
| [HuminoidPOC_Plan.docx](HuminoidPOC_Plan.docx) | v1 — Full 2-day build plan with steps and commands |
| [Architecture_Design_Document.docx](Architecture_Design_Document.docx) | v1 — Component diagram, data flow, design decisions |
| [PRD.docx](PRD.docx) | v1 — Product requirements, user stories, acceptance criteria |
