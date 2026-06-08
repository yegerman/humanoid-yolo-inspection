"""
Main demo: runs the full inspection loop in the MuJoCo interactive viewer.

Usage:
    python demo.py [--scene standalone|full] [--no-viewer]

Controls (in viewer window):
    Space  — pause/resume simulation
    Q      — quit

A separate OpenCV window shows the annotated head-cam feed.
Parts spawn on the table every SPAWN_INTERVAL seconds.
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

import cv2
import mujoco
import mujoco.viewer
import numpy as np

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from vision.detector import Detector
from robot.inspection_controller import InspectionController, State

SCENE_STANDALONE = str(ROOT / "scene" / "inspection_scene_standalone.xml")
SCENE_FULL       = str(ROOT / "scene" / "inspection_scene.xml")

IMG_W, IMG_H = 640, 480
SPAWN_INTERVAL = 5.0     # seconds between part spawns
SIM_RATE       = 250     # Hz (dt=0.004)


def load_scene(scene_path: str):
    model = mujoco.MjModel.from_xml_path(scene_path)
    data  = mujoco.MjData(model)
    return model, data


def render_head_cam(renderer: mujoco.Renderer,
                    model: mujoco.MjModel,
                    data:  mujoco.MjData) -> np.ndarray:
    renderer.update_scene(data, camera="head_cam")
    rgb = renderer.render()
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def draw_overlay(img: np.ndarray, status) -> np.ndarray:
    lines = [
        f"State:    {status.state.name}",
        f"Inspected:{status.total_parts}",
        f"Defects:  {status.defects_found}",
        f"Picks:    {status.picks_done}",
    ]
    if status.last_class:
        lines.append(f"Last:     {status.last_class} ({status.last_conf:.2f})")

    y = 22
    for line in lines:
        cv2.putText(img, line, (8, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (240, 240, 240), 1, cv2.LINE_AA)
        y += 22

    # State indicator bar
    colour_map = {
        State.WATCHING:    (50,  200, 50),
        State.APPROACHING: (50,  200, 200),
        State.PICKING:     (200, 200, 50),
        State.DROPPING:    (200, 100, 50),
        State.RETURNING:   (50,  100, 200),
    }
    bar_colour = colour_map.get(status.state, (150, 150, 150))
    cv2.rectangle(img, (0, 0), (IMG_W, 5), bar_colour, -1)

    return img


def run_demo(scene_path: str, use_viewer: bool):
    print(f"Loading scene: {scene_path}")
    model, data = load_scene(scene_path)

    print("Loading detector …")
    try:
        detector = Detector()
    except FileNotFoundError as e:
        print(f"\n[WARNING] {e}")
        print("Running in VISION-DISABLED mode (arm will not move on detections).")
        detector = None

    renderer = mujoco.Renderer(model, height=IMG_H, width=IMG_W)

    if detector:
        controller = InspectionController(model, data, detector)
    else:
        controller = None

    last_spawn  = 0.0
    next_class  = 0
    frame_count = 0
    last_detect_frame: np.ndarray | None = None

    print("\nStarting simulation …")
    print("Press Ctrl+C in terminal to stop.\n")

    def sim_loop(viewer_handle=None):
        nonlocal last_spawn, next_class, frame_count, last_detect_frame

        start_wall = time.perf_counter()

        while True:
            sim_time = data.time

            # Spawn a new part every SPAWN_INTERVAL seconds
            if controller and sim_time - last_spawn >= SPAWN_INTERVAL:
                class_id = next_class % 3
                next_class += 1
                spawned = controller.spawn_part(class_id)
                if spawned:
                    class_names = {0: "good", 1: "defect_crack", 2: "defect_discolor"}
                    print(f"[SPAWN] {class_names[class_id]} (t={sim_time:.1f}s)")
                last_spawn = sim_time

            # Render head cam at ~10 fps for vision
            do_vision = (frame_count % 25 == 0)
            if do_vision:
                frame_bgr = render_head_cam(renderer, model, data)
                last_detect_frame = frame_bgr

            # Step controller
            if controller and last_detect_frame is not None and do_vision:
                status = controller.step(sim_time, last_detect_frame)
            elif controller:
                status = controller.step(sim_time, None)
            else:
                status = None

            # Display annotated cam window
            if do_vision and last_detect_frame is not None:
                display = last_detect_frame.copy()
                if detector and do_vision:
                    result = detector.detect(last_detect_frame, annotate=True)
                    display = result.frame_annotated if result.frame_annotated is not None else display
                if status:
                    display = draw_overlay(display, status)
                cv2.imshow("Head Camera", display)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            # Step physics
            mujoco.mj_step(model, data)
            frame_count += 1

            # Sync with viewer
            if viewer_handle is not None:
                if not viewer_handle.is_running():
                    break
                viewer_handle.sync()

            # Print metrics every 30 seconds
            elapsed_wall = time.perf_counter() - start_wall
            if elapsed_wall > 0 and frame_count % (SIM_RATE * 30) == 0 and status:
                fps = frame_count / elapsed_wall
                print(f"\n[METRICS] t={sim_time:.0f}s  "
                      f"inspected={status.total_parts}  "
                      f"defects={status.defects_found}  "
                      f"picks={status.picks_done}  "
                      f"sim_fps={fps:.0f}")

    if use_viewer:
        with mujoco.viewer.launch_passive(model, data) as viewer:
            viewer.cam.distance = 2.5
            viewer.cam.elevation = -25
            viewer.cam.azimuth = 160
            sim_loop(viewer)
    else:
        # Headless: run for 60 sim seconds, save output frames
        out_dir = ROOT / "output"
        out_dir.mkdir(exist_ok=True)
        print(f"Headless mode: saving annotated frames to {out_dir}")

        target_frames = 60 * SIM_RATE  # 60 seconds of sim time
        frame_idx = 0

        def headless_sim_loop():
            nonlocal frame_idx, last_spawn, next_class, frame_count, last_detect_frame
            while frame_count < target_frames:
                sim_time = data.time
                if controller and sim_time - last_spawn >= SPAWN_INTERVAL:
                    class_id = next_class % 3
                    next_class += 1
                    controller.spawn_part(class_id)
                    last_spawn = sim_time

                do_vision = (frame_count % 25 == 0)
                if do_vision:
                    frame_bgr = render_head_cam(renderer, model, data)
                    last_detect_frame = frame_bgr
                    if controller:
                        status = controller.step(sim_time, frame_bgr)
                    else:
                        status = None

                    if status:
                        display = frame_bgr.copy()
                        if detector:
                            result = detector.detect(frame_bgr, annotate=True)
                            display = result.frame_annotated if result.frame_annotated is not None else display
                        display = draw_overlay(display, status)
                        cv2.imwrite(str(out_dir / f"frame_{frame_idx:05d}.jpg"),
                                    display, [cv2.IMWRITE_JPEG_QUALITY, 85])
                        frame_idx += 1

                mujoco.mj_step(model, data)
                frame_count += 1

        headless_sim_loop()
        print(f"Saved {frame_idx} frames to {out_dir}")

    renderer.close()
    cv2.destroyAllWindows()
    print("\nDemo finished.")
    if controller:
        s = controller.step(0, None)
        print(f"Final metrics: inspected={s.total_parts}  "
              f"defects={s.defects_found}  picks={s.picks_done}")


def main():
    parser = argparse.ArgumentParser(description="Humanoid Inspection POC Demo")
    parser.add_argument("--scene", choices=["standalone", "full"],
                        default="standalone",
                        help="standalone=no G1 needed; full=requires unitree_mujoco")
    parser.add_argument("--no-viewer", action="store_true",
                        help="Headless mode: save output frames instead of opening viewer")
    args = parser.parse_args()

    scene_path = SCENE_FULL if args.scene == "full" else SCENE_STANDALONE
    if not Path(scene_path).exists():
        sys.exit(f"Scene file not found: {scene_path}")

    run_demo(scene_path, use_viewer=not args.no_viewer)


if __name__ == "__main__":
    main()
