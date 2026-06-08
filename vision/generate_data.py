"""
Synthetic data generation: renders 2000 labeled frames from MuJoCo
offscreen renderer. Outputs JPEG images + YOLO .txt label files.

Usage:
    python vision/generate_data.py [--n 2000] [--scene standalone]
"""

import argparse
import os
import random
import sys
from pathlib import Path

import cv2
import mujoco
import numpy as np

ROOT = Path(__file__).parent.parent
SCENE_STANDALONE = str(ROOT / "scene" / "inspection_scene_standalone.xml")
SCENE_FULL = str(ROOT / "scene" / "inspection_scene.xml")

IMG_W, IMG_H = 640, 480
FOVY = 60.0

CLASS_NAMES = {0: "good", 1: "defect_crack", 2: "defect_discolor"}
# part body names in the XML, indexed by class id
PART_BODIES = {0: "part_0", 1: "part_1", 2: "part_2"}
PART_GEOMS  = {0: "part_0_geom", 1: "part_1_geom", 2: "part_2_geom"}

# Good / crack / discolor RGBA
PART_COLORS = {
    0: np.array([0.2,  0.75, 0.2,  1.0]),
    1: np.array([0.85, 0.1,  0.1,  1.0]),
    2: np.array([0.25, 0.25, 0.25, 1.0]),
}

TABLE_Z = 0.78  # top surface of table


def random_part_pos() -> np.ndarray:
    """Random XY on table surface with small jitter."""
    x = 0.85 + random.uniform(-0.22, 0.22)
    y = random.uniform(-0.15, 0.15)
    return np.array([x, y, TABLE_Z + 0.025])


def set_part_pose(model: mujoco.MjModel, data: mujoco.MjData,
                  class_id: int, pos: np.ndarray):
    """Move the active part body onto the table; hide the others below."""
    for cid, bname in PART_BODIES.items():
        bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, bname)
        jid = model.body_jntadr[bid]  # freejoint address
        if jid < 0:
            continue
        qadr = model.jnt_qposadr[jid]
        if cid == class_id:
            data.qpos[qadr:qadr+3] = pos
            data.qpos[qadr+3:qadr+7] = [1, 0, 0, 0]  # unit quaternion
        else:
            data.qpos[qadr:qadr+3] = [pos[0], pos[1], -5.0]


def set_part_color(model: mujoco.MjModel, class_id: int,
                   noise: float = 0.05):
    """Randomise material colour slightly around the class base colour."""
    for cid, gname in PART_GEOMS.items():
        gid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, gname)
        if gid < 0:
            continue
        if cid == class_id:
            base = PART_COLORS[cid].copy()
            jitter = np.random.uniform(-noise, noise, 3)
            base[:3] = np.clip(base[:3] + jitter, 0.0, 1.0)
            model.geom_rgba[gid] = base
        else:
            model.geom_rgba[gid][3] = 0.0   # invisible


def randomise_lighting(model: mujoco.MjModel, data: mujoco.MjData):
    """Scale light diffuse values randomly."""
    for name in ["light_main", "light_fill"]:
        lid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_LIGHT, name)
        if lid < 0:
            continue
        scale = random.uniform(0.5, 1.8)
        model.light_diffuse[lid] = np.clip(model.light_diffuse[lid] * scale, 0, 1)


def project_point(model: mujoco.MjModel, data: mujoco.MjData,
                  world_pos: np.ndarray, camera: str) -> tuple[float, float] | None:
    """Project a 3-D world point to normalised image coords [0,1]."""
    cam_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, camera)
    if cam_id < 0:
        return None

    # Camera frame from data.cam_xmat (row-major rotation matrix)
    R = data.cam_xmat[cam_id].reshape(3, 3)   # world→cam rotation
    t = data.cam_xpos[cam_id]                  # cam position in world

    p_cam = R.T @ (world_pos - t)              # point in camera frame

    if p_cam[2] <= 0:
        return None

    f = (IMG_H / 2.0) / np.tan(np.deg2rad(FOVY / 2.0))
    u = 0.5 + (p_cam[0] / p_cam[2]) * f / IMG_W
    v = 0.5 - (p_cam[1] / p_cam[2]) * f / IMG_H
    return u, v


def yolo_label(cx: float, cy: float, half_w: float, half_h: float) -> str:
    return f"{cx:.6f} {cy:.6f} {half_w*2:.6f} {half_h*2:.6f}"


def render_dataset(scene_path: str, n_total: int, out_root: Path):
    model = mujoco.MjModel.from_xml_path(scene_path)
    data  = mujoco.MjData(model)

    renderer = mujoco.Renderer(model, height=IMG_H, width=IMG_W)

    train_split = int(n_total * 0.85)

    counts = {0: 0, 1: 0, 2: 0}
    # Distribute classes: ~600 good, ~700 crack, ~700 discolor
    targets = {0: round(n_total * 0.30),
               1: round(n_total * 0.35),
               2: n_total - round(n_total * 0.30) - round(n_total * 0.35)}

    indices = []
    for cid, cnt in targets.items():
        indices.extend([cid] * cnt)
    random.shuffle(indices)

    img_train = out_root / "images" / "train"
    img_val   = out_root / "images" / "val"
    lbl_train = out_root / "labels" / "train"
    lbl_val   = out_root / "labels" / "val"
    for d in [img_train, img_val, lbl_train, lbl_val]:
        d.mkdir(parents=True, exist_ok=True)

    print(f"Rendering {n_total} frames to {out_root} …")

    for i, class_id in enumerate(indices):
        mujoco.mj_resetData(model, data)

        pos = random_part_pos()
        set_part_pose(model, data, class_id, pos)
        set_part_color(model, class_id)
        randomise_lighting(model, data)

        mujoco.mj_forward(model, data)

        renderer.update_scene(data, camera="head_cam")
        img_rgb = renderer.render()   # HxWx3 uint8

        # Compute projected bounding box (part is 0.04×0.04×0.025 box)
        corners_world = []
        for dx in [-0.04, 0.04]:
            for dy in [-0.04, 0.04]:
                corners_world.append(pos + np.array([dx, dy, 0.0]))

        uv_list = [project_point(model, data, c, "head_cam") for c in corners_world]
        uv_list = [uv for uv in uv_list if uv is not None]

        split = "train" if i < train_split else "val"
        img_dir = img_train if split == "train" else img_val
        lbl_dir = lbl_train if split == "train" else lbl_val

        fname = f"{class_id}_{i:05d}"
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(img_dir / f"{fname}.jpg"), img_bgr,
                    [cv2.IMWRITE_JPEG_QUALITY, 92])

        if uv_list:
            us = [uv[0] for uv in uv_list]
            vs = [uv[1] for uv in uv_list]
            cx = np.mean(us)
            cy = np.mean(vs)
            half_w = (max(us) - min(us)) / 2 * 1.3  # 30% padding
            half_h = (max(vs) - min(vs)) / 2 * 1.3
            cx = np.clip(cx, 0, 1)
            cy = np.clip(cy, 0, 1)
            half_w = min(half_w, min(cx, 1-cx))
            half_h = min(half_h, min(cy, 1-cy))
            label_line = f"{class_id} {yolo_label(cx, cy, half_w, half_h)}\n"
        else:
            label_line = ""

        with open(lbl_dir / f"{fname}.txt", "w") as f:
            f.write(label_line)

        counts[class_id] += 1
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{n_total}  good={counts[0]}  crack={counts[1]}  discolor={counts[2]}")

    renderer.close()
    print(f"\nDone. Images written to {out_root}/images/{{train,val}}")
    print(f"Labels written to {out_root}/labels/{{train,val}}")
    print(f"Class totals: {counts}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=2000, help="Total frames to render")
    parser.add_argument("--scene", choices=["standalone", "full"], default="standalone")
    args = parser.parse_args()

    scene = SCENE_STANDALONE if args.scene == "standalone" else SCENE_FULL
    if not Path(scene).exists():
        sys.exit(f"Scene file not found: {scene}")

    render_dataset(scene, args.n, ROOT / "data")


if __name__ == "__main__":
    main()
