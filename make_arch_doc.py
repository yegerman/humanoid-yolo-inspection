"""Generates Architecture_Design_Document.docx"""

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from pathlib import Path
import subprocess, sys

OUT      = r"C:\huminoid\Architecture_Design_Document.docx"
DIAG_PNG = r"C:\huminoid\output\architecture_diagram.png"

# Generate diagram first
subprocess.run([sys.executable, r"C:\huminoid\make_arch_diagram.py"], check=True)

BLUE_DARK  = RGBColor(0x1F, 0x49, 0x7D)
BLUE_MID   = RGBColor(0x2E, 0x75, 0xB6)
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
GREEN      = RGBColor(0x70, 0xAD, 0x47)
ORANGE     = RGBColor(0xED, 0x7D, 0x31)
PURPLE     = RGBColor(0x70, 0x30, 0xA0)


def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def add_rule(doc, color="2E75B6", sz=12):
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bot = OxmlElement("w:bottom")
    bot.set(qn("w:val"), "single"); bot.set(qn("w:sz"), str(sz))
    bot.set(qn("w:space"), "1");   bot.set(qn("w:color"), color)
    pBdr.append(bot); pPr.append(pBdr)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(3)


def h1(doc, text):
    p = doc.add_heading(text, level=1)
    for r in p.runs:
        r.font.color.rgb = BLUE_DARK; r.font.size = Pt(15)
        r.font.name = "Arial"; r.font.bold = True
    p.paragraph_format.space_before = Pt(16); p.paragraph_format.space_after = Pt(4)
    add_rule(doc)


def h2(doc, text):
    p = doc.add_heading(text, level=2)
    for r in p.runs:
        r.font.color.rgb = BLUE_MID; r.font.size = Pt(12)
        r.font.name = "Arial"; r.font.bold = True
    p.paragraph_format.space_before = Pt(10); p.paragraph_format.space_after = Pt(3)


def para(doc, text, bold=False, italic=False, size=11, indent=0):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.name = "Arial"; r.font.size = Pt(size)
    r.bold = bold; r.italic = italic
    if indent: p.paragraph_format.left_indent = Inches(indent)
    p.paragraph_format.space_after = Pt(4)


def bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet")
    r = p.add_run(text)
    r.font.name = "Arial"; r.font.size = Pt(10.5)
    p.paragraph_format.left_indent = Inches(0.3 + level * 0.25)
    p.paragraph_format.space_after = Pt(2)


def code(doc, lines):
    for line in lines:
        p = doc.add_paragraph()
        r = p.add_run(line or " ")
        r.font.name = "Courier New"; r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(0x1E, 0x1E, 0x1E)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.left_indent = Inches(0.3)
        rPr = r._r.get_or_add_rPr()
        shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), "EBEBEB")
        rPr.append(shd)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def table(doc, headers, rows, widths=None):
    t = doc.add_table(rows=1+len(rows), cols=len(headers))
    t.style = "Table Grid"
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        set_cell_bg(cell, "1F497D")
        p = cell.paragraphs[0]; p.clear()
        r = p.add_run(h); r.font.bold = True
        r.font.color.rgb = WHITE; r.font.name = "Arial"; r.font.size = Pt(9.5)
        p.paragraph_format.space_before = Pt(3); p.paragraph_format.space_after = Pt(3)
    for ri, row in enumerate(rows):
        fill = "F2F2F2" if ri % 2 else "FFFFFF"
        for ci, val in enumerate(row):
            cell = t.rows[ri+1].cells[ci]
            set_cell_bg(cell, fill)
            p = cell.paragraphs[0]; p.clear()
            r = p.add_run(str(val))
            r.font.name = "Arial"; r.font.size = Pt(9.5)
            p.paragraph_format.space_before = Pt(3); p.paragraph_format.space_after = Pt(3)
    if widths:
        for i, w in enumerate(widths):
            for row in t.rows:
                row.cells[i].width = int(w * 914400)
    doc.add_paragraph()


def add_footer(doc):
    for section in doc.sections:
        footer = section.footer
        p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        p.clear(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run("Humanoid Inspection POC  |  Architecture Design Document  |  Page ")
        r.font.name = "Arial"; r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
        for tag in ["begin", "end"]:
            fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), tag)
            r2 = p.add_run(); r2.font.name="Arial"; r2.font.size=Pt(8.5)
            r2.font.color.rgb=RGBColor(0x99,0x99,0x99); r2._r.append(fc)
        instr = OxmlElement("w:instrText"); instr.text = "PAGE"
        r3 = p.add_run(); r3.font.name="Arial"; r3.font.size=Pt(8.5)
        r3.font.color.rgb=RGBColor(0x99,0x99,0x99); r3._r.append(instr)


# ── BUILD DOC ────────────────────────────────────────────────────────────────
doc = Document()
for section in doc.sections:
    section.top_margin = Inches(1.0); section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.15); section.right_margin = Inches(1.15)

# Title page
doc.add_paragraph()
doc.add_paragraph()
tp = doc.add_paragraph(); tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = tp.add_run("Architecture Design Document")
r.font.name="Arial"; r.font.size=Pt(26); r.font.bold=True; r.font.color.rgb=BLUE_DARK

sp = doc.add_paragraph(); sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = sp.add_run("Humanoid Robot Industrial Inspection POC")
r.font.name="Arial"; r.font.size=Pt(15); r.font.color.rgb=BLUE_MID

doc.add_paragraph()
add_rule(doc, "2E75B6", 18)
doc.add_paragraph()

mp = doc.add_paragraph(); mp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = mp.add_run("Version 1.0  ·  June 2026  ·  C:\\huminoid")
r.font.name="Arial"; r.font.size=Pt(10); r.font.color.rgb=RGBColor(0x55,0x55,0x55)
doc.add_page_break()

# 1. Overview
h1(doc, "1. System Overview")
para(doc,
    "The Humanoid Robot Inspection POC is a closed-loop simulation system in which a "
    "Unitree G1 humanoid robot performs autonomous visual quality inspection at a work "
    "table. The system spans four architectural layers: simulation core, vision pipeline, "
    "control layer, and data/training pipeline. An optional cloud augmentation path "
    "connects to NVIDIA's Cosmos 3 NIM API to enrich synthetic training data with "
    "photorealistic industrial textures.")
para(doc,
    "All compute runs locally on a Windows PC with an AMD RX 580 GPU (CPU physics + "
    "OpenGL rendering). No NVIDIA GPU is required at runtime — Cosmos 3 is accessed "
    "over HTTP only during the offline training phase.")

# 2. Architecture Diagram
h1(doc, "2. Architecture Diagram")
if Path(DIAG_PNG).exists():
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(DIAG_PNG, width=Inches(6.5))
    cap = doc.add_paragraph("Figure 1 — Four-layer system architecture showing data flow between components")
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in cap.runs:
        r.font.size=Pt(9); r.font.italic=True; r.font.color.rgb=RGBColor(0x66,0x66,0x66)
    doc.add_paragraph()
else:
    para(doc, "[Diagram not found — run make_arch_diagram.py first]", italic=True)

# 3. Layers
h1(doc, "3. Architectural Layers")

h2(doc, "3.1  Simulation Core")
para(doc,
    "MuJoCo 3.9 provides deterministic rigid-body physics at 250 Hz. The simulation "
    "scene is defined in two XML files: a standalone version (placeholder capsule robot) "
    "and a full version that includes the Unitree G1 MJCF. Both share the same world "
    "geometry: a work table, a reject bin, three part bodies with free joints, and "
    "a head-mounted camera.")
table(doc,
    ["Component", "File", "Role"],
    [
        ["MuJoCo Engine",   "mujoco 3.9.0 (pip)",                  "Physics stepping, collision, rendering"],
        ["Standalone scene","scene/inspection_scene_standalone.xml","Self-contained scene for testing without G1"],
        ["Full scene",      "scene/inspection_scene.xml",           "Includes G1 MJCF via <include>"],
        ["Offscreen render","mujoco.Renderer (640×480)",            "Generates head-cam frames for vision"],
        ["Interactive view","mujoco.viewer.launch_passive",         "Real-time 3D display for demo"],
    ], [1.5, 2.5, 2.8])

h2(doc, "3.2  Vision Pipeline")
para(doc,
    "YOLOv8n (Nano) runs on CPU at ~80 ms/frame. The Detector class wraps ultralytics, "
    "loads the best.onnx exported model, and returns DetectionResult objects containing "
    "class ID, confidence, and bounding box. Inference is throttled to every 5th "
    "simulation step (~10 fps) to avoid saturating the CPU.")
table(doc,
    ["Component", "File", "Notes"],
    [
        ["Detector",        "vision/detector.py",      "Wraps YOLO, returns DetectionResult"],
        ["Model (train)",   "runs/train/weights/best.pt","PyTorch checkpoint"],
        ["Model (runtime)", "runs/train/weights/best.onnx","ONNX export — faster CPU inference"],
        ["Annotator",       "vision/detector.py _draw()","Draws bboxes + HUD on BGR frame"],
        ["OpenCV window",   "demo.py",                 "Displays annotated head-cam feed"],
    ], [1.5, 2.5, 2.8])

h2(doc, "3.3  Control Layer")
para(doc,
    "The inspection controller implements a 5-state finite state machine decoupled "
    "from the physics loop. Each call to step(sim_time, frame) advances the state "
    "machine and writes target joint angles to data.ctrl[] via the IK solver.")
table(doc,
    ["State", "Trigger", "Duration", "Arm Action"],
    [
        ["WATCHING",    "Entry / return",         "Continuous",  "Home pose; YOLO runs every 200 ms"],
        ["APPROACHING", "Defect detected",        "1.5 s",       "Blend to reach_table keyframe"],
        ["PICKING",     "APPROACHING timeout",    "1.0 s",       "Hold reach pose; remove part"],
        ["DROPPING",    "PICKING timeout",        "1.0 s",       "Blend to drop_bin keyframe"],
        ["RETURNING",   "DROPPING timeout",       "1.2 s",       "Blend back to home keyframe"],
    ], [1.4, 1.8, 1.0, 2.6])

para(doc,
    "The IK solver (robot/ik_solver.py) operates in one of two modes: Damped Least "
    "Squares (DLS) online IK when the G1 MJCF is loaded (7-DOF right arm, λ=0.05, "
    "50 iterations), or keyframe interpolation fallback for the standalone scene. "
    "All three keyframe poses (home, reach_table, drop_bin) are smooth-step interpolated "
    "over the state duration.")

h2(doc, "3.4  Data / Training Pipeline")
para(doc,
    "Training data is generated entirely from the MuJoCo offscreen renderer, "
    "eliminating the need for real-world images. Each frame is automatically labeled "
    "by projecting the known part position through the camera model.")
table(doc,
    ["Stage", "Script", "Output"],
    [
        ["Offscreen render",  "vision/generate_data.py",  "2,000 JPEG frames + YOLO .txt labels"],
        ["Cosmos augment",    "vision/augment_cosmos.py", "500 photorealistic variants (optional)"],
        ["YOLO fine-tune",    "vision/train_yolo.py",     "best.pt + best.onnx (50 epochs, CPU)"],
        ["Dataset config",    "data/dataset.yaml",        "3 classes: good / defect_crack / defect_discolor"],
    ], [1.6, 2.4, 2.8])

h2(doc, "3.5  Cloud Augmentation (Cosmos 3 NIM)")
para(doc,
    "NVIDIA's Cosmos 3 Diffusion model is accessed via the NIM HTTP API at "
    "ai.api.nvidia.com. Synthetic MuJoCo frames are encoded as base64 and sent with "
    "an industrial-context prompt. The returned image has photorealistic factory "
    "floor textures applied (image-to-image diffusion, strength=0.6). Bounding box "
    "labels are preserved unchanged since geometry is not altered. This step is "
    "optional but improves sim-to-real generalization.")
code(doc, [
    "POST ai.api.nvidia.com/v1/genai/nvidia/cosmos-1.0-diffusion",
    '{"image": "<base64>", "prompt": "industrial factory floor...", "strength": 0.6}',
])

# 4. Data Flow
h1(doc, "4. Runtime Data Flow")
para(doc, "Each simulation step (4 ms) executes the following sequence:")
for i, step in enumerate([
    "MuJoCo physics step (mj_step) — advances simulation by 4 ms",
    "Every 25th step: Renderer.update_scene() + render() → BGR frame (10 fps)",
    "InspectionController.step(sim_time, frame) called each step",
    "If WATCHING and 200 ms elapsed: Detector.detect(frame) → DetectionResult",
    "If defect found: state → APPROACHING; IKSolver.interpolate_to_pose() called",
    "IKSolver.apply_pose() writes to data.ctrl[] → MuJoCo actuator targets",
    "MuJoCo viewer synced via viewer.sync() — renders updated joint positions",
    "OpenCV window updated with annotated frame + state HUD overlay",
], 1):
    bullet(doc, f"{i+1}.  {step}")

doc.add_paragraph()

# 5. Module Interface Table
h1(doc, "5. Module Interfaces")
table(doc,
    ["Module", "Inputs", "Outputs", "Key Class/Function"],
    [
        ["vision/detector.py",              "BGR frame (np.ndarray)",    "DetectionResult",        "Detector.detect()"],
        ["robot/ik_solver.py",              "target_pos (np.ndarray)",   "IKResult / pose dict",   "IKSolver.solve()"],
        ["robot/inspection_controller.py",  "sim_time, BGR frame",       "ControllerStatus",       "InspectionController.step()"],
        ["vision/generate_data.py",         "MuJoCo model + renderer",   "JPEG frames + .txt",     "render_dataset()"],
        ["vision/train_yolo.py",            "dataset.yaml",              "best.pt + best.onnx",    "train()"],
        ["vision/augment_cosmos.py",        "JPEG frames + API key",     "Augmented JPEGs",        "cosmos_augment()"],
        ["demo.py",                         "scene XML path",            "Viewer + OpenCV window", "run_demo()"],
    ], [1.8, 1.9, 1.7, 1.9])

# 6. Dependency Graph
h1(doc, "6. Dependency Graph")
code(doc, [
    "demo.py",
    "  ├── vision/detector.py          (ultralytics, opencv-python)",
    "  ├── robot/inspection_controller.py",
    "  │     ├── robot/ik_solver.py    (mujoco, numpy, scipy)",
    "  │     └── vision/detector.py",
    "  └── mujoco                      (physics + viewer + renderer)",
    "",
    "vision/train_yolo.py",
    "  └── ultralytics                 (torch, torchvision)",
    "",
    "vision/generate_data.py",
    "  └── mujoco, opencv-python, numpy",
    "",
    "vision/augment_cosmos.py",
    "  └── requests, Pillow            (NVIDIA NIM API — network only)",
])

# 7. File Map
h1(doc, "7. File Map")
table(doc,
    ["Path", "Type", "Description"],
    [
        ["scene/inspection_scene_standalone.xml", "MuJoCo XML", "Self-contained scene — placeholder robot, no G1 MJCF needed"],
        ["scene/inspection_scene.xml",            "MuJoCo XML", "Full scene — includes G1 MJCF via <include>"],
        ["vision/generate_data.py",               "Python",     "Offscreen renderer loop; auto-projects YOLO labels"],
        ["vision/augment_cosmos.py",              "Python",     "Calls Cosmos NIM HTTP API; polite rate limiting"],
        ["vision/train_yolo.py",                  "Python",     "YOLOv8n fine-tune; merges augmented images before train"],
        ["vision/detector.py",                    "Python",     "Detector class; prefers ONNX over .pt at runtime"],
        ["robot/ik_solver.py",                    "Python",     "DLS IK (G1) + keyframe fallback (standalone)"],
        ["robot/inspection_controller.py",        "Python",     "5-state FSM; spawns/removes parts; drives arm"],
        ["demo.py",                               "Python",     "Main entry; viewer + OpenCV cam window + spawn loop"],
        ["verify_setup.py",                       "Python",     "Pre-flight check: imports, scene load, model presence"],
        ["data/dataset.yaml",                     "YAML",       "YOLO dataset config — 3 classes, train/val split"],
    ], [2.8, 1.0, 3.0])

# 8. Design Decisions
h1(doc, "8. Key Design Decisions")
table(doc,
    ["Decision", "Chosen Approach", "Alternative Considered", "Rationale"],
    [
        ["Simulator",        "MuJoCo 3.x",           "Isaac Sim",           "Isaac Sim requires NVIDIA GPU — not available on AMD RX 580"],
        ["Vision model",     "YOLOv8n (CPU)",         "YOLOv8s / MobileNet", "Nano: ~80 ms/frame on i7; small enough for CPU real-time"],
        ["IK method",        "DLS + keyframe fallback","ROS2 MoveIt",        "No ROS2 dependency; keyframes sufficient for POC pick-place"],
        ["Training data",    "MuJoCo offscreen render","Real imagery",        "No real robot needed; 2,000 frames in ~5 min"],
        ["Augmentation",     "Cosmos 3 NIM (cloud)",  "Local diffusion model","AMD GPU can't run Cosmos locally; cloud API costs ~$0.02/image"],
        ["Project path",     "C:\\huminoid",          "E:\\huminoid",        "E:\\ drive is full (0 bytes); short path avoids MuJoCo Windows bug"],
    ], [1.4, 1.6, 1.7, 2.1])

add_footer(doc)
doc.save(OUT)
print(f"Saved: {OUT}")
