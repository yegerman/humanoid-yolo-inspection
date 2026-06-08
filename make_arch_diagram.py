"""Generates architecture_diagram.png — called by make_arch_doc.py"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

OUT = r"C:\huminoid\output\architecture_diagram.png"

import pathlib
pathlib.Path(r"C:\huminoid\output").mkdir(exist_ok=True)

fig, ax = plt.subplots(figsize=(16, 10))
ax.set_xlim(0, 16)
ax.set_ylim(0, 10)
ax.axis("off")
fig.patch.set_facecolor("#F8F9FA")
ax.set_facecolor("#F8F9FA")

# ── colour palette ──────────────────────────────────────────────────────────
C_SIM    = "#1F497D"   # dark blue  — simulation layer
C_VISION = "#2E75B6"   # mid blue   — vision layer
C_CTRL   = "#70AD47"   # green      — control layer
C_DATA   = "#ED7D31"   # orange     — data / training
C_CLOUD  = "#7030A0"   # purple     — cloud / external
C_WHITE  = "#FFFFFF"
C_ARROW  = "#444444"
C_ARROW2 = "#888888"


def box(ax, x, y, w, h, label, sublabel="", color=C_SIM, fontsize=10):
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle="round,pad=0.08",
                          facecolor=color, edgecolor="white",
                          linewidth=2, zorder=3)
    ax.add_patch(rect)
    if sublabel:
        ax.text(x + w/2, y + h*0.62, label,
                ha="center", va="center", fontsize=fontsize,
                fontweight="bold", color=C_WHITE, zorder=4)
        ax.text(x + w/2, y + h*0.28, sublabel,
                ha="center", va="center", fontsize=fontsize - 2,
                color="#DDDDFF", zorder=4, style="italic")
    else:
        ax.text(x + w/2, y + h/2, label,
                ha="center", va="center", fontsize=fontsize,
                fontweight="bold", color=C_WHITE, zorder=4,
                multialignment="center")


def arrow(ax, x1, y1, x2, y2, label="", color=C_ARROW, style="->"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color,
                                lw=1.8, connectionstyle="arc3,rad=0.0"),
                zorder=2)
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx + 0.08, my + 0.08, label,
                fontsize=7.5, color=color, zorder=5,
                ha="left", va="bottom",
                bbox=dict(boxstyle="round,pad=0.15", fc="#F8F9FA",
                          ec="none", alpha=0.85))


def curved_arrow(ax, x1, y1, x2, y2, label="", color=C_ARROW, rad=0.25):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color,
                                lw=1.6,
                                connectionstyle=f"arc3,rad={rad}"),
                zorder=2)
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx + 0.1, my, label,
                fontsize=7.5, color=color, zorder=5,
                ha="left", va="center",
                bbox=dict(boxstyle="round,pad=0.15", fc="#F8F9FA",
                          ec="none", alpha=0.85))


# ── layer background bands ───────────────────────────────────────────────────
def band(ax, y, h, label, color):
    rect = FancyBboxPatch((0.2, y), 15.6, h,
                          boxstyle="round,pad=0.05",
                          facecolor=color, edgecolor="none",
                          alpha=0.10, zorder=1)
    ax.add_patch(rect)
    ax.text(0.38, y + h/2, label, fontsize=8, color=color,
            va="center", alpha=0.7, fontweight="bold", rotation=90)

band(ax, 0.3,  2.2, "DATA / TRAINING",  C_DATA)
band(ax, 2.7,  2.5, "VISION PIPELINE",  C_VISION)
band(ax, 5.4,  2.2, "CONTROL LAYER",    C_CTRL)
band(ax, 7.8,  1.9, "SIMULATION CORE",  C_SIM)

# ── title ────────────────────────────────────────────────────────────────────
ax.text(8, 9.6, "Humanoid Robot Inspection POC — Architecture",
        ha="center", va="center", fontsize=15,
        fontweight="bold", color=C_SIM)
ax.text(8, 9.25, "Unitree G1  ·  MuJoCo 3.x  ·  YOLOv8n  ·  Cosmos 3 NIM API",
        ha="center", va="center", fontsize=10, color="#555555")


# ── LAYER 4: Simulation Core (top) ──────────────────────────────────────────
box(ax, 0.8,  8.0, 2.8, 1.5, "MuJoCo 3.x\nPhysics Engine",
    "CPU, 250 Hz step", C_SIM)
box(ax, 4.0,  8.0, 2.6, 1.5, "Inspection Scene\nXML",
    "table · bin · parts", C_SIM)
box(ax, 7.0,  8.0, 2.6, 1.5, "G1 Robot\nMJCF Model",
    "23 DOF · freejoint parts", C_SIM)
box(ax, 10.0, 8.0, 2.6, 1.5, "Offscreen\nRenderer",
    "640×480 · head_cam", C_SIM)
box(ax, 13.0, 8.0, 2.6, 1.5, "MuJoCo\nViewer",
    "interactive 3D display", C_SIM, fontsize=9)

# ── LAYER 3: Control Layer ───────────────────────────────────────────────────
box(ax, 0.8,  5.6, 2.8, 1.5, "Inspection\nController",
    "5-state machine", C_CTRL)
box(ax, 4.2,  5.6, 2.6, 1.5, "IK Solver",
    "DLS / keyframe fallback", C_CTRL)
box(ax, 7.4,  5.6, 2.6, 1.5, "State Machine",
    "WATCH→PICK→DROP", C_CTRL)
box(ax, 10.6, 5.6, 2.6, 1.5, "Arm Pose\nInterpolator",
    "home / reach / drop_bin", C_CTRL)

# ── LAYER 2: Vision Pipeline ─────────────────────────────────────────────────
box(ax, 0.8,  2.9, 2.8, 1.5, "YOLOv8n\nDetector",
    "CPU · ONNX · 480px", C_VISION)
box(ax, 4.2,  2.9, 2.6, 1.5, "Detection\nResult",
    "class · conf · bbox", C_VISION)
box(ax, 7.4,  2.9, 2.6, 1.5, "OpenCV\nAnnotator",
    "bbox overlay · HUD", C_VISION)
box(ax, 10.6, 2.9, 2.6, 1.5, "Frame\nCapture",
    "BGR · 10 fps sample", C_VISION)

# ── LAYER 1: Data / Training (bottom) ───────────────────────────────────────
box(ax, 0.8,  0.5, 2.6, 1.6, "generate_data.py",
    "2000 frames + labels", C_DATA, fontsize=9)
box(ax, 4.0,  0.5, 2.6, 1.6, "train_yolo.py",
    "YOLOv8n finetune", C_DATA, fontsize=9)
box(ax, 7.2,  0.5, 2.6, 1.6, "Dataset\n1700 train / 300 val",
    "3 classes · YOLO format", C_DATA, fontsize=9)
box(ax, 10.4, 0.5, 2.6, 1.6, "best.pt / best.onnx",
    "exported weights", C_DATA, fontsize=9)

# Cosmos cloud box — right side, spans layers 1-2
box(ax, 13.2, 0.5, 2.5, 3.0, "Cosmos 3\nNIM API",
    "build.nvidia.com\nHTTP augmentation", C_CLOUD, fontsize=9)

# ── arrows: simulation layer ─────────────────────────────────────────────────
arrow(ax, 3.6, 8.75, 4.0, 8.75, "loads")
arrow(ax, 6.6, 8.75, 7.0, 8.75, "includes")
arrow(ax, 9.6, 8.75, 10.0, 8.75, "renders")
arrow(ax, 12.6, 8.75, 13.0, 8.75, "displays")

# offscreen renderer → frame capture (down)
arrow(ax, 11.3, 8.0, 11.3, 4.4, "RGB frame", C_VISION)

# ── arrows: vision layer ──────────────────────────────────────────────────────
arrow(ax, 3.6, 3.65, 4.2, 3.65, "detections")
arrow(ax, 6.8, 3.65, 7.4, 3.65, "annotate")
arrow(ax, 13.2, 2.0, 10.6+2.6, 2.0, "augmented\nframes", C_CLOUD)
arrow(ax, 13.2, 2.0, 13.2, 0.5+3.0, "", C_CLOUD)

# frame capture → detector
arrow(ax, 10.6, 3.65, 3.6, 3.65, "BGR frame", C_VISION)

# detector → controller (up)
arrow(ax, 2.2, 4.4, 2.2, 5.6, "defect\ndetected", C_CTRL)

# ── arrows: control layer ─────────────────────────────────────────────────────
arrow(ax, 3.6, 6.35, 4.2, 6.35, "target pos")
arrow(ax, 6.8, 6.35, 7.4, 6.35, "transition")
arrow(ax, 10.0, 6.35, 10.6, 6.35, "pose blend")

# controller → MuJoCo data.ctrl (up)
arrow(ax, 5.5, 7.1, 5.5, 8.0, "data.ctrl[]", C_SIM)

# ── arrows: data/training ─────────────────────────────────────────────────────
arrow(ax, 3.4, 1.3, 4.0, 1.3, "frames")
arrow(ax, 6.6, 1.3, 7.2, 1.3, "dataset")
arrow(ax, 9.8, 1.3, 10.4, 1.3, "trains →")

# training data → offscreen renderer (loop)
curved_arrow(ax, 2.1, 8.0, 1.5, 2.1, "sim renders", C_DATA, rad=0.0)

# Cosmos → dataset
curved_arrow(ax, 13.2, 1.5, 9.8, 1.5, "+500 aug\nframes", C_CLOUD, rad=-0.15)

# trained model → detector (left side loop)
curved_arrow(ax, 0.8, 1.3, 0.8, 3.65, "loads\nweights", C_VISION, rad=-0.4)

# ── legend ───────────────────────────────────────────────────────────────────
legend_items = [
    mpatches.Patch(color=C_SIM,    label="Simulation Core"),
    mpatches.Patch(color=C_CTRL,   label="Control Layer"),
    mpatches.Patch(color=C_VISION, label="Vision Pipeline"),
    mpatches.Patch(color=C_DATA,   label="Data / Training"),
    mpatches.Patch(color=C_CLOUD,  label="Cloud API (Cosmos 3)"),
]
ax.legend(handles=legend_items, loc="upper right",
          bbox_to_anchor=(0.99, 0.97),
          fontsize=8.5, framealpha=0.9,
          facecolor="white", edgecolor="#CCCCCC")

plt.tight_layout(pad=0.3)
plt.savefig(OUT, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close()
print(f"Saved diagram: {OUT}")
