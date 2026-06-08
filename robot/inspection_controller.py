"""
Inspection state machine: WATCHING → DETECT → APPROACHING → PICKING → DROPPING → RETURNING

Decoupled from the viewer loop: call step(dt, frame_bgr) every sim step.
Returns a ControllerState that the demo can render as overlay text.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

import numpy as np

from robot.ik_solver import (IKSolver, POSE_HOME, POSE_REACH_TABLE,
                              POSE_DROP_BIN, NAMED_POSES)

try:
    import mujoco
    _HAS_MUJOCO = True
except ImportError:
    _HAS_MUJOCO = False


class State(Enum):
    WATCHING    = auto()
    APPROACHING = auto()
    PICKING     = auto()
    DROPPING    = auto()
    RETURNING   = auto()


# Duration of each state (seconds)
STATE_DURATIONS = {
    State.APPROACHING: 1.5,
    State.PICKING:     1.0,
    State.DROPPING:    1.0,
    State.RETURNING:   1.2,
}

DETECT_INTERVAL = 0.20   # run YOLO every 200ms
TABLE_SURFACE_Z = 0.78
BIN_POS = np.array([-0.5, 0.7, 0.20])   # drop target above reject bin


@dataclass
class ControllerStatus:
    state:         State
    state_elapsed: float
    total_parts:   int
    defects_found: int
    picks_done:    int
    last_class:    str = ""
    last_conf:     float = 0.0
    arm_pose:      str = POSE_HOME


class InspectionController:
    """
    Wires vision.Detector + robot.IKSolver into a timed state machine.

    Parameters
    ----------
    model / data : MuJoCo model + data (pass None for headless / test mode)
    detector     : vision.Detector instance
    """

    def __init__(self,
                 model: Optional["mujoco.MjModel"],
                 data:  Optional["mujoco.MjData"],
                 detector):
        self._model    = model
        self._data     = data
        self._detector = detector
        self._ik       = IKSolver(model, data)

        self._state         = State.WATCHING
        self._state_start   = time.perf_counter()
        self._last_detect   = 0.0
        self._current_part: Optional[object] = None   # last Detection

        self._total_parts  = 0
        self._defects_found = 0
        self._picks_done   = 0
        self._current_pose = POSE_HOME

        # Spawn part index cycling through bodies 0/1/2
        self._part_idx     = 0
        self._part_on_table: Optional[int] = None   # body index currently on table

    # ------------------------------------------------------------------
    # Main update — call every sim step
    # ------------------------------------------------------------------

    def step(self, sim_time: float, frame_bgr: Optional[np.ndarray]) -> ControllerStatus:
        now = time.perf_counter()
        elapsed = now - self._state_start

        if self._state == State.WATCHING:
            self._step_watching(now, frame_bgr)

        elif self._state == State.APPROACHING:
            self._blend_arm(POSE_REACH_TABLE, elapsed,
                            STATE_DURATIONS[State.APPROACHING])
            if elapsed >= STATE_DURATIONS[State.APPROACHING]:
                self._transition(State.PICKING)

        elif self._state == State.PICKING:
            self._blend_arm(POSE_REACH_TABLE, elapsed,
                            STATE_DURATIONS[State.PICKING])
            if elapsed >= STATE_DURATIONS[State.PICKING]:
                self._picks_done += 1
                self._remove_part_from_table()
                self._transition(State.DROPPING)

        elif self._state == State.DROPPING:
            self._blend_arm(POSE_DROP_BIN, elapsed,
                            STATE_DURATIONS[State.DROPPING])
            if elapsed >= STATE_DURATIONS[State.DROPPING]:
                self._transition(State.RETURNING)

        elif self._state == State.RETURNING:
            self._blend_arm(POSE_HOME, elapsed,
                            STATE_DURATIONS[State.RETURNING])
            if elapsed >= STATE_DURATIONS[State.RETURNING]:
                self._transition(State.WATCHING)

        return ControllerStatus(
            state=self._state,
            state_elapsed=now - self._state_start,
            total_parts=self._total_parts,
            defects_found=self._defects_found,
            picks_done=self._picks_done,
            last_class=self._current_part.label if self._current_part else "",
            last_conf=self._current_part.confidence if self._current_part else 0.0,
            arm_pose=self._current_pose,
        )

    # ------------------------------------------------------------------
    # State step: WATCHING
    # ------------------------------------------------------------------

    def _step_watching(self, now: float, frame_bgr: Optional[np.ndarray]):
        if frame_bgr is None:
            return
        if now - self._last_detect < DETECT_INTERVAL:
            return

        self._last_detect = now
        result = self._detector.detect(frame_bgr, annotate=False)

        if result.best_defect is not None:
            det = result.best_defect
            self._current_part = det
            self._defects_found += 1
            self._total_parts += 1
            print(f"[DETECT] {det.label} conf={det.confidence:.2f} "
                  f"→ initiating pick")
            self._transition(State.APPROACHING)

    # ------------------------------------------------------------------
    # Arm blending
    # ------------------------------------------------------------------

    def _blend_arm(self, target_pose_name: str, elapsed: float, duration: float):
        t = min(elapsed / max(duration, 1e-6), 1.0)
        # Smooth step
        t = t * t * (3 - 2 * t)

        pose = self._ik.interpolate_to_pose(target_pose_name, t)
        self._ik.apply_pose(pose)
        self._current_pose = target_pose_name

    # ------------------------------------------------------------------
    # Scene helpers
    # ------------------------------------------------------------------

    def spawn_part(self, class_id: int,
                   pos: Optional[np.ndarray] = None) -> bool:
        """Move a part body onto the table. Returns True on success."""
        if self._model is None or self._data is None:
            return False

        if pos is None:
            import random
            x = 0.85 + random.uniform(-0.18, 0.18)
            y = random.uniform(-0.12, 0.12)
            pos = np.array([x, y, TABLE_SURFACE_Z + 0.025])

        body_name = f"part_{class_id}"
        bid = mujoco.mj_name2id(
            self._model, mujoco.mjtObj.mjOBJ_BODY, body_name)
        if bid < 0:
            return False

        jid = self._model.body_jntadr[bid]
        if jid < 0:
            return False

        qadr = self._model.jnt_qposadr[jid]
        self._data.qpos[qadr:qadr+3] = pos
        self._data.qpos[qadr+3:qadr+7] = [1, 0, 0, 0]
        self._data.qvel[self._model.jnt_dofadr[jid]:
                        self._model.jnt_dofadr[jid]+6] = 0
        mujoco.mj_forward(self._model, self._data)

        self._part_on_table = class_id
        self._part_idx = class_id
        return True

    def _remove_part_from_table(self):
        """Move the current part out of scene (under the floor)."""
        if (self._model is None or self._data is None
                or self._part_on_table is None):
            return

        body_name = f"part_{self._part_on_table}"
        bid = mujoco.mj_name2id(
            self._model, mujoco.mjtObj.mjOBJ_BODY, body_name)
        if bid < 0:
            return

        jid = self._model.body_jntadr[bid]
        if jid < 0:
            return

        qadr = self._model.jnt_qposadr[jid]
        self._data.qpos[qadr:qadr+3] = [0, 0, -5.0]
        mujoco.mj_forward(self._model, self._data)
        self._part_on_table = None

    # ------------------------------------------------------------------

    def _transition(self, new_state: State):
        print(f"[STATE] {self._state.name} → {new_state.name}")
        self._state       = new_state
        self._state_start = time.perf_counter()
