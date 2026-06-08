"""Generates HuminoidPOC_Plan.docx — run once then delete."""

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

OUT = r"C:\huminoid\HuminoidPOC_Plan.docx"

# ── colour palette ────────────────────────────────────────────────────────────
BLUE_DARK  = RGBColor(0x1F, 0x49, 0x7D)   # title / heading 1
BLUE_MID   = RGBColor(0x2E, 0x75, 0xB6)   # heading 2
BLUE_LIGHT = RGBColor(0xBD, 0xD7, 0xEE)   # table header fill
GREY_LIGHT = RGBColor(0xF2, 0xF2, 0xF2)   # alternate row fill
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
BLACK      = RGBColor(0x00, 0x00, 0x00)


# ── helpers ───────────────────────────────────────────────────────────────────

def set_cell_bg(cell, hex_color: str):
    """Set table cell background colour (hex without #)."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def set_col_width(table, col_idx: int, width_twips: int):
    for row in table.rows:
        row.cells[col_idx].width = width_twips


def add_horizontal_rule(doc, color_hex="2E75B6", thickness=12):
    """Add a coloured horizontal rule paragraph."""
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(thickness))
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), color_hex)
    pBdr.append(bottom)
    pPr.append(pBdr)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(4)
    return p


def heading1(doc, text):
    p = doc.add_heading(text, level=1)
    for run in p.runs:
        run.font.color.rgb = BLUE_DARK
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.name = "Arial"
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after  = Pt(6)
    add_horizontal_rule(doc)
    return p


def heading2(doc, text):
    p = doc.add_heading(text, level=2)
    for run in p.runs:
        run.font.color.rgb = BLUE_MID
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.name = "Arial"
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after  = Pt(4)
    return p


def body(doc, text, bold=False, italic=False, size=11, indent=False):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = "Arial"
    run.font.size = Pt(size)
    run.bold  = bold
    run.italic = italic
    if indent:
        p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.space_after = Pt(4)
    return p


def bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet")
    run = p.add_run(text)
    run.font.name = "Arial"
    run.font.size = Pt(11)
    p.paragraph_format.left_indent  = Inches(0.3 + level * 0.25)
    p.paragraph_format.space_after  = Pt(2)
    return p


def code_block(doc, lines):
    """Monospaced code-style paragraph(s)."""
    for line in lines:
        p = doc.add_paragraph()
        run = p.add_run(line if line else " ")
        run.font.name = "Courier New"
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x1E, 0x1E, 0x1E)
        p.paragraph_format.space_after  = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.left_indent  = Inches(0.3)
        # light grey background on the run
        rPr = run._r.get_or_add_rPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), "EBEBEB")
        rPr.append(shd)


def make_table(doc, headers, rows, col_widths_inches=None):
    """Build a styled table with blue header row and alternating row colours."""
    n_cols = len(headers)
    table = doc.add_table(rows=1 + len(rows), cols=n_cols)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.LEFT

    # Header row
    hdr = table.rows[0]
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        set_cell_bg(cell, "1F497D")
        p = cell.paragraphs[0]
        p.clear()
        run = p.add_run(h)
        run.font.bold  = True
        run.font.color.rgb = WHITE
        run.font.name  = "Arial"
        run.font.size  = Pt(10)
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after  = Pt(3)

    # Data rows
    for r_idx, row_data in enumerate(rows):
        row = table.rows[r_idx + 1]
        fill = "F2F2F2" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, cell_text in enumerate(row_data):
            cell = row.cells[c_idx]
            set_cell_bg(cell, fill)
            p = cell.paragraphs[0]
            p.clear()
            run = p.add_run(str(cell_text))
            run.font.name = "Arial"
            run.font.size = Pt(10)
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after  = Pt(3)

    # Column widths
    if col_widths_inches:
        for i, w in enumerate(col_widths_inches):
            for row in table.rows:
                row.cells[i].width = int(w * 914400)  # inches → EMU then to twips via docx

    doc.add_paragraph()   # spacing after table
    return table


# ── document ──────────────────────────────────────────────────────────────────

doc = Document()

# Page margins
for section in doc.sections:
    section.top_margin    = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin   = Inches(1.15)
    section.right_margin  = Inches(1.15)

# ── Title page ────────────────────────────────────────────────────────────────
doc.add_paragraph()
doc.add_paragraph()

title_p = doc.add_paragraph()
title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title_p.add_run("Humanoid Robot Industrial Inspection")
run.font.name  = "Arial"
run.font.size  = Pt(28)
run.font.bold  = True
run.font.color.rgb = BLUE_DARK

sub_p = doc.add_paragraph()
sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = sub_p.add_run("2-Day Proof of Concept — Unitree G1 + MuJoCo")
run.font.name  = "Arial"
run.font.size  = Pt(16)
run.font.color.rgb = BLUE_MID

doc.add_paragraph()
add_horizontal_rule(doc, "2E75B6", 18)
doc.add_paragraph()

meta_p = doc.add_paragraph()
meta_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = meta_p.add_run("Project path: C:\\huminoid     |     Date: June 2026")
run.font.name  = "Arial"
run.font.size  = Pt(11)
run.font.color.rgb = RGBColor(0x44, 0x44, 0x44)

doc.add_page_break()

# ── 1. Executive Summary ──────────────────────────────────────────────────────
heading1(doc, "1. Executive Summary")
body(doc,
     "This POC demonstrates a Unitree G1 humanoid robot performing automated visual "
     "quality inspection at a simulated industrial work station. The robot's head-mounted "
     "camera continuously inspects parts placed on a work table, classifying each as "
     "good or defective. When a defect is detected, the robot's right arm reaches to the "
     "table, picks up the defective part, and deposits it in a reject bin — closing a "
     "full pick-and-place inspection loop entirely in simulation.")
body(doc,
     "The simulation runs in MuJoCo 3.x (CPU physics, AMD-compatible OpenGL rendering) "
     "on a Windows PC with an AMD RX 580 GPU. Training data is generated synthetically "
     "from the simulator, then optionally enriched with photorealistic industrial textures "
     "via NVIDIA's Cosmos 3 cloud API (NIM). The complete demo targets a 2-day build "
     "timeline and is designed to convey a clear industrial ROI story.")

# ── 2. Hardware Overview ──────────────────────────────────────────────────────
heading1(doc, "2. Hardware Overview")
make_table(doc,
    ["Component", "Spec", "Assessment"],
    [
        ["CPU",     "Intel i7-6700, 4-core 3.4 GHz", "Fine for MuJoCo CPU physics"],
        ["RAM",     "16 GB DDR4",                    "Adequate — reduce batch to 4 if pressure"],
        ["GPU",     "AMD RX 580 8 GB",               "OpenGL rendering only (no CUDA/NVIDIA)"],
        ["Storage", "466 GB SSD",                    "Use SSD path — HDD too slow for I/O"],
        ["OS",      "Windows 10 Pro 64-bit",         "Supported; use short paths for MuJoCo"],
    ],
    col_widths_inches=[1.5, 2.5, 2.8]
)
body(doc,
     "Note: Isaac Sim requires an NVIDIA GPU and is not viable on this hardware. "
     "MuJoCo is the correct simulator for this setup.", italic=True)

# ── 3. Tech Stack ─────────────────────────────────────────────────────────────
heading1(doc, "3. Tech Stack")
make_table(doc,
    ["Component", "Tool", "Rationale"],
    [
        ["Simulation",         "MuJoCo 3.x",                    "CPU physics, OpenGL, AMD-compatible, Windows support"],
        ["Robot model",        "Unitree G1 MJCF",               "Official MJCF from unitree_mujoco repo"],
        ["Vision",             "YOLOv8n (ultralytics, CPU)",    "Nano model: ~80 ms/frame on i7-6700"],
        ["Control",            "Python MuJoCo bindings + IK",   "No ROS2 needed; DLS IK + keyframe fallback"],
        ["Visualization",      "MuJoCo viewer + OpenCV",        "Native 3D viewer + annotated camera window"],
        ["Data generation",    "MuJoCo offscreen renderer",     "2,000 labeled frames with auto-projected YOLO labels"],
        ["Scene augmentation", "Cosmos 3 via NVIDIA NIM API",   "HTTP call to build.nvidia.com — no local GPU needed"],
    ],
    col_widths_inches=[1.8, 2.4, 2.6]
)
body(doc,
     "Cosmos 3 (NVIDIA NIM API): Cosmos 3 cannot run locally on AMD hardware, but NVIDIA "
     "hosts it as a cloud API. Synthetic MuJoCo frames are sent over HTTP and returned "
     "with photorealistic industrial textures/lighting applied. Free trial credits are "
     "available at build.nvidia.com; estimated cost ~$0.01–0.05 per image.", italic=True)

# ── 4. POC Concept ────────────────────────────────────────────────────────────
heading1(doc, "4. POC Concept: Defect Detection at Work Table")
body(doc,
     "The G1 humanoid robot stands beside a work table. Inspection parts appear on the "
     "table one at a time (spawned by the simulation script every 5 seconds). The robot's "
     "head camera runs YOLOv8n inference every 200 ms and classifies each part:")

make_table(doc,
    ["Class ID", "Label", "Visual Appearance", "Robot Action"],
    [
        ["0", "good",            "Green box",              "Arm stays at home pose"],
        ["1", "defect_crack",    "Red box (crack texture)", "Arm reaches, picks, drops in reject bin"],
        ["2", "defect_discolor", "Dark grey box",          "Arm reaches, picks, drops in reject bin"],
    ],
    col_widths_inches=[0.8, 1.6, 2.2, 2.2]
)
body(doc,
     "Why a table instead of a conveyor: A static work table is simpler to model in "
     "MuJoCo in one day. A conveyor requires custom geom physics. The table setup "
     "demonstrates identical industrial logic — a cell inspection station — with less "
     "implementation risk.", italic=True)

# ── 5. Repository Structure ───────────────────────────────────────────────────
heading1(doc, "5. Repository Structure")
body(doc, "All files located at C:\\huminoid  (E:\\ drive is full — 0 bytes free)", bold=True)
doc.add_paragraph()

code_block(doc, [
    "C:\\huminoid\\",
    "├── scene\\",
    "│   ├── inspection_scene_standalone.xml   ← self-contained scene (no G1 needed)",
    "│   └── inspection_scene.xml              ← full scene (requires unitree_mujoco)",
    "├── data\\",
    "│   ├── dataset.yaml                      ← YOLO dataset config",
    "│   ├── images\\{train,val}\\               ← rendered JPEG frames",
    "│   ├── labels\\{train,val}\\               ← YOLO .txt label files",
    "│   └── augmented\\                        ← Cosmos-augmented frames",
    "├── vision\\",
    "│   ├── generate_data.py                  ← offscreen render + auto-label",
    "│   ├── augment_cosmos.py                 ← Cosmos NIM API augmentation",
    "│   ├── train_yolo.py                     ← YOLOv8n fine-tune (CPU mode)",
    "│   └── detector.py                       ← live detection class",
    "├── robot\\",
    "│   ├── ik_solver.py                      ← DLS IK + keyframe fallback",
    "│   └── inspection_controller.py          ← 5-state inspection machine",
    "├── demo.py                               ← main entry: viewer + control loop",
    "├── verify_setup.py                       ← environment sanity check",
    "└── requirements.txt",
])
doc.add_paragraph()

# ── 6. Day 1 Plan ─────────────────────────────────────────────────────────────
heading1(doc, "6. Day 1 Plan")

heading2(doc, "Step 1 — Python Environment Setup  (1 h)")
bullet(doc, "Install Python 3.11 (avoid 3.12 for MuJoCo compatibility)")
bullet(doc, "Create and activate virtual environment:")
code_block(doc, [
    "python -m venv .venv",
    ".venv\\Scripts\\activate",
    "pip install -r requirements.txt",
])
body(doc, "Key packages: mujoco>=3.1.0, ultralytics>=8.2.0, opencv-python, numpy, scipy, dm_control, requests")

heading2(doc, "Step 2 — Get Unitree G1 MJCF Model  (30 min)")
bullet(doc, "Clone the official Unitree MuJoCo repository:")
code_block(doc, [
    "git clone https://github.com/unitreerobotics/unitree_mujoco.git C:\\unitree_mujoco",
])
bullet(doc, "G1 model files located at: C:\\unitree_mujoco\\unitree_robots\\g1\\")
bullet(doc, "Fallback: use inspection_scene_standalone.xml (no G1 required) if MJCF has issues")

heading2(doc, "Step 3 — Build MuJoCo Scene  (2–3 h)")
bullet(doc, "Two scene files are provided — standalone (placeholder robot) and full (G1 MJCF)")
bullet(doc, "Scene includes: work table, reject bin, 3 part bodies, head camera site, 3 lights")
bullet(doc, "Verify standalone scene loads:")
code_block(doc, [
    "python -m mujoco.viewer --mjcf scene\\inspection_scene_standalone.xml",
])

heading2(doc, "Step 4 — Synthetic Data Generation  (2 h)")
bullet(doc, "Run generate_data.py to render 2,000 labeled frames via MuJoCo offscreen renderer")
bullet(doc, "Randomises: part position on table, light intensity (0.5–2.0×), part colour jitter")
bullet(doc, "Auto-generates YOLO bounding boxes from camera projection matrix")
bullet(doc, "Target distribution: ~600 good / ~700 defect_crack / ~700 defect_discolor")
code_block(doc, [
    "python vision\\generate_data.py --n 2000",
])

heading2(doc, "Step 4b — Cosmos 3 Augmentation via NIM API  (1 h, optional)")
bullet(doc, "Sign up at https://build.nvidia.com to get an API key (free trial credits included)")
bullet(doc, "Augments 500 of the 2,000 synthetic frames with photorealistic industrial textures")
bullet(doc, "Bridges the sim-to-real gap without a local NVIDIA GPU")
code_block(doc, [
    "$env:NVIDIA_API_KEY = \"nvapi-xxxx\"",
    "python vision\\augment_cosmos.py --n 500 --strength 0.6",
])

heading2(doc, "Step 5 — YOLOv8n Training  (1–2 h)")
bullet(doc, "Fine-tunes YOLOv8n on the synthetic dataset; runs entirely on CPU")
bullet(doc, "Expected training time: ~1.5 h for 50 epochs on i7-6700")
bullet(doc, "Exports best checkpoint to ONNX for faster CPU inference")
code_block(doc, [
    "python vision\\train_yolo.py --epochs 50 --batch 8 --imgsz 480",
    "# Reduce --batch to 4 if RAM pressure occurs",
])

# ── 7. Day 2 Plan ─────────────────────────────────────────────────────────────
heading1(doc, "7. Day 2 Plan")

heading2(doc, "Step 6 — IK Solver for G1 Right Arm  (2–3 h)")
bullet(doc, "robot/ik_solver.py implements two modes:")
bullet(doc, "DLS (Damped Least Squares) IK — full online IK when G1 MJCF is loaded", level=1)
bullet(doc, "Keyframe fallback — 3 pre-baked poses interpolated linearly (home / reach_table / drop_bin)", level=1)
bullet(doc, "Joint limits enforced for all 7 right-arm joints per G1 spec")
bullet(doc, "POC simplification: pre-computed waypoint poses are sufficient; exact IK precision is not critical")

heading2(doc, "Step 7 — Inspection Control Loop  (2 h)")
body(doc, "robot/inspection_controller.py implements a 5-state machine:")
doc.add_paragraph()
code_block(doc, [
    "WATCHING     → run YOLOv8 on head cam every 200 ms",
    "  ↓ defect detected (confidence > 0.45)",
    "APPROACHING  → blend arm to reach_table pose  (1.5 s)",
    "PICKING      → hold reach pose, simulate grasp  (1.0 s)",
    "DROPPING     → blend arm to drop_bin pose  (1.0 s)",
    "RETURNING    → blend arm back to home  (1.2 s)",
    "  ↓",
    "WATCHING     (loop)",
])
doc.add_paragraph()
bullet(doc, "All transitions are timed (no joint-space feedback required for POC)")
bullet(doc, "State machine decoupled from viewer loop — call step(dt, frame) each sim step")

heading2(doc, "Step 8 — Main Demo  (2 h)")
bullet(doc, "demo.py launches MuJoCo interactive viewer (3D) + OpenCV head-cam window side by side")
bullet(doc, "Parts spawn on table every 5 seconds (cycling through all 3 classes)")
bullet(doc, "Detection bounding boxes drawn on OpenCV window with class label and confidence")
bullet(doc, "Console prints state transitions and 30-second metric summaries")
code_block(doc, [
    "# Standalone scene (no G1 MJCF needed)",
    "python demo.py --scene standalone",
    "",
    "# Full scene with G1",
    "python demo.py --scene full",
    "",
    "# Headless (saves annotated frames to output\\)",
    "python demo.py --scene standalone --no-viewer",
])

heading2(doc, "Step 9 — Demo Polish  (1 h)")
bullet(doc, "Record demo video using OBS Studio or Windows Game Bar (Win+G)")
bullet(doc, "Prepare 5-slide deck: Problem → Solution → Architecture → Live Demo → Next Steps")
bullet(doc, "Highlight Cosmos 3 augmentation slide: sim-to-real gap bridged via cloud API")

# ── 8. Success Criteria ───────────────────────────────────────────────────────
heading1(doc, "8. Success Criteria")
make_table(doc,
    ["Metric", "Target", "Measurement"],
    [
        ["Defect detection mAP",  "> 80%",          "YOLOv8 validation set at end of training"],
        ["False positive rate",   "< 20%",           "Good parts incorrectly flagged as defects"],
        ["Arm reach success",     "> 70% of defects","Arm visibly reaches table area on detection"],
        ["Inference latency",     "< 150 ms/frame",  "Detector.detect() wall-clock time logged"],
        ["Full loop stability",   "5 min crash-free","demo.py running in viewer without exception"],
    ],
    col_widths_inches=[2.2, 1.4, 3.2]
)

# ── 9. Key Commands ───────────────────────────────────────────────────────────
heading1(doc, "9. Key Commands")

heading2(doc, "Day 1 — Environment & Training")
code_block(doc, [
    "cd C:\\huminoid",
    "python -m venv .venv",
    ".venv\\Scripts\\activate",
    "pip install -r requirements.txt",
    "",
    "# Verify install",
    "python verify_setup.py",
    "",
    "# Generate training data",
    "python vision\\generate_data.py --n 2000",
    "",
    "# Optional: Cosmos augmentation",
    "$env:NVIDIA_API_KEY = \"nvapi-xxxx\"",
    "python vision\\augment_cosmos.py --n 500",
    "",
    "# Train YOLOv8n",
    "python vision\\train_yolo.py --epochs 50 --batch 8",
])

heading2(doc, "Day 2 — Demo")
code_block(doc, [
    "# Quick scene test (no G1 MJCF required)",
    "python -m mujoco.viewer --mjcf scene\\inspection_scene_standalone.xml",
    "",
    "# Full demo",
    "python demo.py --scene standalone",
    "",
    "# With G1 MJCF (after cloning unitree_mujoco)",
    "python demo.py --scene full",
])

# ── 10. Risks & Mitigations ───────────────────────────────────────────────────
heading1(doc, "10. Risks & Mitigations")
make_table(doc,
    ["Risk", "Likelihood", "Mitigation"],
    [
        ["G1 MJCF model fails to load",
         "Medium",
         "Use inspection_scene_standalone.xml — placeholder robot demonstrates full pipeline"],
        ["YOLOv8 CPU inference too slow (>200 ms)",
         "Low",
         "Drop to 5 fps inference; load ONNX model instead of .pt; demo still looks smooth"],
        ["IK does not converge on table targets",
         "Medium",
         "Pre-baked keyframe poses (home/reach_table/drop_bin) are used by default — exact IK not required"],
        ["16 GB RAM pressure during training",
         "Low",
         "Reduce batch to 4; reduce dataset to 1,000 images; disable cache=True in train_yolo.py"],
        ["Windows path issues with MuJoCo",
         "Low",
         "Project at C:\\huminoid (short path). E:\\ drive is full — do not use E:\\ paths"],
    ],
    col_widths_inches=[2.6, 1.0, 3.2]
)

# ── 11. Future Upgrade Path ───────────────────────────────────────────────────
heading1(doc, "11. Future Upgrade Path")
body(doc, "When NVIDIA GPU access is available (cloud VM or local hardware):")
doc.add_paragraph()

make_table(doc,
    ["Phase", "Action", "Benefit"],
    [
        ["Post-POC",
         "Port scene to NVIDIA Isaac Sim",
         "RTX ray tracing, photorealistic rendering, ROS2 integration"],
        ["Post-POC",
         "Run Cosmos 3 Nano (16B) locally",
         "Faster augmentation, private, no API cost or rate limits"],
        ["Month 1–2",
         "Real robot deployment on physical G1",
         "Transfer trained YOLOv8 weights + IK controller to hardware"],
        ["Month 2–3",
         "Conveyor belt scene + online retraining",
         "Continuous-flow inspection; model improves from real detections"],
    ],
    col_widths_inches=[1.2, 2.6, 3.0]
)

# ── Footer on all pages ───────────────────────────────────────────────────────
from docx.oxml.ns import nsmap as _nsmap

def add_footer(doc):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    for section in doc.sections:
        footer = section.footer
        p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        p.clear()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        run = p.add_run("Humanoid Inspection POC  |  C:\\huminoid  |  June 2026  |  Page ")
        run.font.name = "Arial"
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x88, 0x88, 0x88)

        # Page number field
        fldChar1 = OxmlElement("w:fldChar")
        fldChar1.set(qn("w:fldCharType"), "begin")
        instrText = OxmlElement("w:instrText")
        instrText.text = "PAGE"
        fldChar2 = OxmlElement("w:fldChar")
        fldChar2.set(qn("w:fldCharType"), "end")
        run2 = p.add_run()
        run2.font.name = "Arial"
        run2.font.size = Pt(9)
        run2.font.color.rgb = RGBColor(0x88, 0x88, 0x88)
        run2._r.append(fldChar1)
        run2._r.append(instrText)
        run2._r.append(fldChar2)

add_footer(doc)

# ── Save ──────────────────────────────────────────────────────────────────────
doc.save(OUT)
print(f"Saved: {OUT}")
