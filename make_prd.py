"""Generates PRD.docx"""

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = r"C:\huminoid\PRD.docx"

BLUE_DARK = RGBColor(0x1F, 0x49, 0x7D)
BLUE_MID  = RGBColor(0x2E, 0x75, 0xB6)
GREEN     = RGBColor(0x70, 0xAD, 0x47)
RED       = RGBColor(0xC0, 0x00, 0x00)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)


def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color); tcPr.append(shd)


def add_rule(doc, color="2E75B6", sz=12):
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bot = OxmlElement("w:bottom")
    bot.set(qn("w:val"), "single"); bot.set(qn("w:sz"), str(sz))
    bot.set(qn("w:space"), "1"); bot.set(qn("w:color"), color)
    pBdr.append(bot); pPr.append(pBdr)
    p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(3)


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


def h3(doc, text):
    p = doc.add_heading(text, level=3)
    for r in p.runs:
        r.font.color.rgb = GREEN; r.font.size = Pt(11)
        r.font.name = "Arial"; r.font.bold = True
    p.paragraph_format.space_before = Pt(8); p.paragraph_format.space_after = Pt(2)


def para(doc, text, bold=False, italic=False, size=11):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.name = "Arial"; r.font.size = Pt(size)
    r.bold = bold; r.italic = italic
    p.paragraph_format.space_after = Pt(4)


def bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet")
    r = p.add_run(text)
    r.font.name = "Arial"; r.font.size = Pt(10.5)
    p.paragraph_format.left_indent = Inches(0.3 + level * 0.25)
    p.paragraph_format.space_after = Pt(2)


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
        r = p.add_run("Humanoid Inspection POC  |  Product Requirements Document  |  June 2026")
        r.font.name = "Arial"; r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(0x99, 0x99, 0x99)


# ── BUILD DOC ────────────────────────────────────────────────────────────────
doc = Document()
for section in doc.sections:
    section.top_margin = Inches(1.0); section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.15); section.right_margin = Inches(1.15)

# Title page
doc.add_paragraph(); doc.add_paragraph()
tp = doc.add_paragraph(); tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = tp.add_run("Product Requirements Document")
r.font.name="Arial"; r.font.size=Pt(26); r.font.bold=True; r.font.color.rgb=BLUE_DARK

sp = doc.add_paragraph(); sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = sp.add_run("Humanoid Robot Industrial Inspection POC")
r.font.name="Arial"; r.font.size=Pt(15); r.font.color.rgb=BLUE_MID

doc.add_paragraph(); add_rule(doc, "2E75B6", 18); doc.add_paragraph()

meta_rows = [
    ("Product",   "Humanoid Robot Inspection POC"),
    ("Version",   "1.0"),
    ("Status",    "In Development"),
    ("Owner",     "Mor Yegerman"),
    ("Date",      "June 2026"),
    ("Horizon",   "2-day POC; demo ready for stakeholder presentation"),
]
t = doc.add_table(rows=len(meta_rows), cols=2)
t.style = "Table Grid"
for i, (k, v) in enumerate(meta_rows):
    set_cell_bg(t.rows[i].cells[0], "DEEAF1")
    p = t.rows[i].cells[0].paragraphs[0]; p.clear()
    r = p.add_run(k); r.font.bold=True; r.font.name="Arial"; r.font.size=Pt(10)
    p2 = t.rows[i].cells[1].paragraphs[0]; p2.clear()
    r2 = p2.add_run(v); r2.font.name="Arial"; r2.font.size=Pt(10)
    for cell in [t.rows[i].cells[0], t.rows[i].cells[1]]:
        cell.paragraphs[0].paragraph_format.space_before = Pt(3)
        cell.paragraphs[0].paragraph_format.space_after  = Pt(3)
    t.rows[i].cells[0].width = int(1.3 * 914400)
    t.rows[i].cells[1].width = int(4.0 * 914400)
doc.add_page_break()

# 1. Executive Summary
h1(doc, "1. Executive Summary")
para(doc,
    "This POC demonstrates that a humanoid robot (Unitree G1) can perform automated "
    "visual quality inspection in a simulated industrial environment, providing a "
    "compelling proof of concept for deploying humanoid robots in manufacturing "
    "inspection cells. The system detects defective parts via a head-mounted camera, "
    "classifies them using a fine-tuned computer vision model, and physically removes "
    "them with the robot arm — closing a full autonomous inspection loop entirely in "
    "simulation, on commodity Windows PC hardware.")
para(doc,
    "The primary goal is a 5-minute stable demo ready for a stakeholder presentation. "
    "The secondary goal is to establish the software architecture and training pipeline "
    "that can be transferred to a real G1 robot post-POC.")

# 2. Problem Statement
h1(doc, "2. Problem Statement")
h2(doc, "2.1  Business Problem")
para(doc,
    "Manual quality inspection on production lines is labour-intensive, inconsistent, "
    "and difficult to scale. Humanoid robots offer the dexterity to operate in existing "
    "work cells without retooling, but deploying them requires demonstrating a credible "
    "software stack before committing to hardware investment.")

h2(doc, "2.2  Technical Problem")
para(doc,
    "Existing humanoid robot demo stacks (Isaac Sim + ROS2) require NVIDIA GPUs and "
    "significant infrastructure. This POC must run on commodity hardware (AMD GPU, "
    "Windows, no ROS2) within a 2-day build timeline, while still producing a "
    "convincing and technically sound demo.")

# 3. Goals and Non-Goals
h1(doc, "3. Goals and Non-Goals")
h2(doc, "3.1  Goals")
for g in [
    "Demonstrate a G1 robot detecting and removing defective parts in simulation",
    "Achieve >80% defect detection mAP on held-out synthetic validation set",
    "Run the full demo loop stably for at least 5 minutes without crashing",
    "Show a plausible path to real robot deployment (same code, different scene)",
    "Produce a shareable demo video and stakeholder presentation deck",
]:
    bullet(doc, g)

h2(doc, "3.2  Non-Goals (POC scope)")
for ng in [
    "Real robot hardware integration — simulation only for this POC",
    "Conveyor belt / moving parts — static table with periodic spawning is sufficient",
    "ROS2 integration — direct MuJoCo Python bindings only",
    "Real-world generalisation — training data is 100% synthetic",
    "Multi-robot / multi-arm scenarios",
    "Production-grade error recovery or safety systems",
]:
    bullet(doc, ng)

# 4. User Stories
h1(doc, "4. User Stories")
table(doc,
    ["ID", "As a...", "I want to...", "So that...", "Priority"],
    [
        ["US-01", "Demo presenter",  "See the robot arm move to pick a defective part", "Stakeholders understand the autonomous loop", "P0"],
        ["US-02", "Demo presenter",  "See bounding boxes on the camera feed in real time", "The vision system is visually convincing", "P0"],
        ["US-03", "Demo presenter",  "See good parts ignored and only defects picked", "The classification is clearly working", "P0"],
        ["US-04", "Demo presenter",  "Run the demo for 5+ minutes without a crash", "The system appears production-ready", "P0"],
        ["US-05", "Demo presenter",  "Show a metrics printout (inspected/defects/picks)", "ROI story is quantified", "P1"],
        ["US-06", "Engineer",        "Run the full pipeline from scratch in one day", "Reproduce and extend the work", "P1"],
        ["US-07", "Engineer",        "Swap in the real G1 MJCF without rewriting control code", "Path to real hardware is clear", "P1"],
        ["US-08", "Stakeholder",     "See a recorded demo video", "Evaluate without attending a live session", "P2"],
    ], [0.5, 1.2, 2.2, 2.1, 0.7])

# 5. Functional Requirements
h1(doc, "5. Functional Requirements")

h2(doc, "5.1  Vision")
table(doc,
    ["ID", "Requirement", "Priority", "Acceptance Criteria"],
    [
        ["FR-V1", "Classify parts into 3 classes: good, defect_crack, defect_discolor", "P0", "mAP > 80% on val set"],
        ["FR-V2", "Run inference on head-cam frames at >= 5 fps", "P0", "Latency < 200 ms per frame on i7-6700"],
        ["FR-V3", "Draw bounding boxes and confidence on OpenCV window", "P0", "Boxes visible on every detection"],
        ["FR-V4", "Only trigger arm action on confidence >= 0.45", "P0", "False positive rate < 20%"],
        ["FR-V5", "Load ONNX model when available (faster than .pt on CPU)", "P1", "ONNX loaded by default if best.onnx exists"],
    ], [0.7, 3.0, 0.7, 2.4])

h2(doc, "5.2  Control")
table(doc,
    ["ID", "Requirement", "Priority", "Acceptance Criteria"],
    [
        ["FR-C1", "State machine transitions: WATCHING→APPROACHING→PICKING→DROPPING→RETURNING", "P0", "All 5 states reachable in single run"],
        ["FR-C2", "Arm reaches work table area on APPROACHING", "P0", "Gripper visually moves toward table (>70% attempts)"],
        ["FR-C3", "Part removed from table during PICKING state", "P0", "Part body moves off-scene after pick"],
        ["FR-C4", "Arm returns to home pose after each pick cycle", "P0", "Home pose reached before next WATCHING"],
        ["FR-C5", "Controller works with standalone scene (no G1 MJCF)", "P1", "demo.py --scene standalone runs without error"],
    ], [0.7, 2.8, 0.7, 2.6])

h2(doc, "5.3  Simulation")
table(doc,
    ["ID", "Requirement", "Priority", "Acceptance Criteria"],
    [
        ["FR-S1", "New part spawns on table every 5 seconds",       "P0", "Part body position updated; visible in viewer"],
        ["FR-S2", "3 part classes visually distinguishable",        "P0", "Green / red / dark grey colours in scene"],
        ["FR-S3", "Reject bin positioned within arm reach",         "P0", "Arm drop pose places part over bin"],
        ["FR-S4", "Head camera field of view covers table surface", "P0", "Table visible in head-cam render at all times"],
    ], [0.7, 2.8, 0.7, 2.6])

h2(doc, "5.4  Training Pipeline")
table(doc,
    ["ID", "Requirement", "Priority", "Acceptance Criteria"],
    [
        ["FR-T1", "Generate >= 2,000 synthetic labeled frames",     "P0", "data/images/train + val populated after generate_data.py"],
        ["FR-T2", "Auto-label from camera projection (no manual annotation)", "P0", "All images have paired .txt label file"],
        ["FR-T3", "YOLOv8n trains to >80% mAP in <= 2 hours on CPU", "P0", "metrics/mAP50 printed at end of training"],
        ["FR-T4", "Export trained model to ONNX",                   "P1", "best.onnx present after train_yolo.py"],
        ["FR-T5", "Cosmos augmentation integrates into training set","P2", "Augmented images merged before train when present"],
    ], [0.7, 2.8, 0.7, 2.6])

# 6. Non-Functional Requirements
h1(doc, "6. Non-Functional Requirements")
table(doc,
    ["Category", "Requirement", "Target"],
    [
        ["Performance",   "Detection latency",              "< 150 ms / frame on i7-6700 (CPU)"],
        ["Performance",   "Physics simulation rate",        ">= 250 Hz (MuJoCo default timestep=0.004)"],
        ["Stability",     "Demo run duration without crash","5 minutes minimum"],
        ["Compatibility", "GPU",                            "AMD RX 580 — no CUDA required at runtime"],
        ["Compatibility", "OS",                             "Windows 10 64-bit"],
        ["Reproducibility","Full pipeline re-run time",     "< 3 hours (generate + train + demo)"],
        ["Portability",   "Scene upgrade path",             "Full G1 MJCF scene loads without code changes"],
        ["Storage",       "Total project disk usage",       "< 3 GB including trained model and dataset"],
    ], [1.5, 2.8, 2.5])

# 7. Milestones
h1(doc, "7. Milestones & Timeline")
table(doc,
    ["Milestone", "Description", "Target", "Status"],
    [
        ["M1 — Environment",    "Python venv + deps installed; verify_setup.py passes",      "Day 1, Hour 1",  "Done"],
        ["M2 — Scene",          "Standalone scene loads in MuJoCo viewer",                   "Day 1, Hour 2",  "Done"],
        ["M3 — Data",           "2,000 labeled frames generated",                            "Day 1, Hour 4",  "Done"],
        ["M4 — Training",       "YOLOv8n reaches >80% mAP; best.onnx exported",             "Day 1, End",     "In Progress"],
        ["M5 — Control loop",   "demo.py runs; arm moves on detection",                     "Day 2, Hour 3",  "Pending"],
        ["M6 — Demo polish",    "5-min stable run; video recorded; deck ready",             "Day 2, End",     "Pending"],
        ["M7 — Full G1 scene",  "G1 MJCF loaded; demo.py --scene full runs",               "Post-Day 2",     "Pending"],
    ], [1.8, 2.8, 1.4, 0.9])

# 8. Risks
h1(doc, "8. Risks")
table(doc,
    ["Risk", "Impact", "Likelihood", "Mitigation"],
    [
        ["G1 MJCF doesn't load on Windows",      "High",   "Medium", "Standalone scene is complete fallback — full demo possible without G1"],
        ["YOLOv8 mAP < 80% after 50 epochs",     "Medium", "Low",    "Increase epochs to 100; add colour jitter augmentation in generate_data.py"],
        ["CPU inference too slow for live demo",  "Medium", "Low",    "ONNX model + 5fps cap; demo still looks smooth at 10fps display"],
        ["16 GB RAM exhausted during training",   "High",   "Low",    "batch=4; cache=False; reduce dataset to 1,000 images"],
        ["Arm doesn't reach table visually",      "High",   "Medium", "Tune reach_table keyframe pose angles in ik_solver.py"],
        ["Cosmos API key unavailable",            "Low",    "Medium", "Skip augmentation — 2,000 synthetic frames alone achieve >80% mAP target"],
    ], [1.9, 0.8, 1.0, 2.9])

# 9. Success Criteria
h1(doc, "9. Definition of Done")
para(doc, "The POC is considered complete when all P0 acceptance criteria are met:", bold=True)
for criterion in [
    "verify_setup.py reports all checks passed",
    "generate_data.py produces 2,000 images with paired labels",
    "train_yolo.py reports mAP50 >= 0.80 on validation set",
    "demo.py --scene standalone runs for 5 minutes without exception",
    "Arm visibly moves to table on >= 70% of defect detections",
    "OpenCV window shows bounding boxes with correct class labels",
    "Demo video recorded (OBS / Windows Game Bar)",
]:
    bullet(doc, criterion)

# 10. Future Work
h1(doc, "10. Post-POC Roadmap")
table(doc,
    ["Phase", "Feature", "Dependency"],
    [
        ["v1.1", "Real G1 MJCF scene (23-DOF)",      "Clone unitree_mujoco; adjust arm keyframes"],
        ["v1.2", "Online Cosmos augmentation loop",   "NVIDIA_API_KEY; augment_cosmos.py already written"],
        ["v2.0", "Isaac Sim port",                    "NVIDIA GPU (cloud VM or local RTX)"],
        ["v2.0", "ROS2 integration",                  "Ubuntu + ROS2 Humble + MoveIt"],
        ["v2.1", "Conveyor belt scene",               "Custom MuJoCo conveyor geom + velocity actuator"],
        ["v3.0", "Real G1 hardware deployment",       "Physical Unitree G1 robot; transfer ONNX weights"],
    ], [0.8, 2.4, 3.6])

add_footer(doc)
doc.save(OUT)
print(f"Saved: {OUT}")
