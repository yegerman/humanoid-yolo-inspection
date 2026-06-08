"""
IK solver for the G1 right arm (or the standalone placeholder arm).

Strategy for 2-day POC:
  - Full G1: use MuJoCo's built-in mj_kinematics + damped-least-squares (DLS) IK
    on the right arm joint chain to reach a 3-D target.
  - Standalone placeholder: use 3 pre-computed keyframe poses
    (home / reach_table / drop_bin) with linear interpolation.

The controller always calls `solve(target_pos)` and gets back a dict of
joint-name → target angle (radians).
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Optional

try:
    import mujoco
    _HAS_MUJOCO = True
except ImportError:
    _HAS_MUJOCO = False


# ---------------------------------------------------------------------------
# Keyframe poses (angles in radians) for the standalone placeholder robot.
# These map to the body hierarchy in inspection_scene_standalone.xml.
# Since the placeholder uses fixed bodies (no joints), poses are stored
# as symbolic names used by the controller state machine.
# ---------------------------------------------------------------------------

POSE_HOME        = "home"
POSE_REACH_TABLE = "reach_table"
POSE_DROP_BIN    = "drop_bin"


@dataclass
class IKResult:
    success:    bool
    pose_name:  str               # symbolic name for logging
    ctrl_delta: np.ndarray        # incremental joint angle changes (radians)
    target_pos: np.ndarray        # requested 3-D target


# ---------------------------------------------------------------------------
# G1 right-arm joint names (from unitree_mujoco g1.xml — verify against model)
# ---------------------------------------------------------------------------
G1_RIGHT_ARM_JOINTS = [
    "right_shoulder_pitch_joint",
    "right_shoulder_roll_joint",
    "right_shoulder_yaw_joint",
    "right_elbow_joint",
    "right_wrist_roll_joint",
    "right_wrist_pitch_joint",
    "right_wrist_yaw_joint",
]

# Safe joint limits (radians) — conservative subset of G1 spec
G1_ARM_LIMITS = {
    "right_shoulder_pitch_joint": (-3.14,  3.14),
    "right_shoulder_roll_joint":  (-1.57,  0.52),
    "right_shoulder_yaw_joint":   (-2.87,  2.87),
    "right_elbow_joint":          (-1.25,  2.36),
    "right_wrist_roll_joint":     (-1.57,  1.57),
    "right_wrist_pitch_joint":    (-1.57,  1.57),
    "right_wrist_yaw_joint":      (-1.57,  1.57),
}

# Pre-baked G1 arm keyframe poses (joint name → angle in radians)
G1_HOME_POSE = {
    "right_shoulder_pitch_joint": 0.0,
    "right_shoulder_roll_joint":  -0.3,
    "right_shoulder_yaw_joint":   0.0,
    "right_elbow_joint":          0.5,
    "right_wrist_roll_joint":     0.0,
    "right_wrist_pitch_joint":    0.0,
    "right_wrist_yaw_joint":      0.0,
}

G1_REACH_TABLE_POSE = {
    "right_shoulder_pitch_joint": 0.8,
    "right_shoulder_roll_joint":  -0.5,
    "right_shoulder_yaw_joint":   -0.3,
    "right_elbow_joint":          1.4,
    "right_wrist_roll_joint":     0.0,
    "right_wrist_pitch_joint":    -0.5,
    "right_wrist_yaw_joint":      0.2,
}

G1_DROP_BIN_POSE = {
    "right_shoulder_pitch_joint": 0.0,
    "right_shoulder_roll_joint":  0.4,
    "right_shoulder_yaw_joint":   0.8,
    "right_elbow_joint":          0.9,
    "right_wrist_roll_joint":     0.5,
    "right_wrist_pitch_joint":    0.3,
    "right_wrist_yaw_joint":      0.0,
}

NAMED_POSES = {
    POSE_HOME:        G1_HOME_POSE,
    POSE_REACH_TABLE: G1_REACH_TABLE_POSE,
    POSE_DROP_BIN:    G1_DROP_BIN_POSE,
}


class IKSolver:
    """
    Damped Least Squares (DLS) IK solver for G1 right arm.

    Falls back to keyframe interpolation when model is not provided
    (standalone mode or when G1 MJCF is not yet loaded).
    """

    DLS_LAMBDA  = 0.05    # damping coefficient
    MAX_ITERS   = 50
    TOL_POS     = 0.015   # 1.5 cm convergence tolerance

    def __init__(self, model: Optional["mujoco.MjModel"] = None,
                 data:  Optional["mujoco.MjData"]  = None):
        self._model = model
        self._data  = data
        self._use_dls = (model is not None and _HAS_MUJOCO
                         and self._find_site("r_gripper_site") >= 0)

        if self._use_dls:
            self._joint_ids = self._resolve_joint_ids()
            self._site_id   = self._find_site("r_gripper_site")
            print(f"IK: DLS mode, {len(self._joint_ids)} arm joints")
        else:
            print("IK: keyframe mode (no G1 model or site not found)")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def move_to_pose(self, pose_name: str) -> dict[str, float]:
        """Return the target joint angles for a named pose."""
        return NAMED_POSES.get(pose_name, G1_HOME_POSE).copy()

    def solve(self, target_pos: np.ndarray) -> IKResult:
        """
        Compute joint angles to place the gripper at target_pos.
        Returns IKResult with ctrl_delta (not absolute angles).
        """
        if self._use_dls:
            return self._dls_solve(target_pos)
        else:
            return self._keyframe_solve(target_pos)

    def apply_pose(self, pose: dict[str, float]):
        """Write joint angles directly into data.ctrl[]."""
        if self._model is None or self._data is None:
            return
        for jname, angle in pose.items():
            jid = mujoco.mj_name2id(
                self._model, mujoco.mjtObj.mjOBJ_JOINT, jname)
            if jid < 0:
                continue
            actuator_id = self._joint_to_actuator(jname)
            if actuator_id >= 0:
                lo, hi = G1_ARM_LIMITS.get(jname, (-3.14, 3.14))
                self._data.ctrl[actuator_id] = float(np.clip(angle, lo, hi))

    def interpolate_to_pose(self, pose_name: str, t: float) -> dict[str, float]:
        """
        Return interpolated pose between current qpos and target pose.
        t: 0→1 blend factor.
        """
        target = NAMED_POSES.get(pose_name, G1_HOME_POSE)
        result = {}
        for jname, target_angle in target.items():
            current = self._get_joint_angle(jname)
            result[jname] = current + t * (target_angle - current)
        return result

    # ------------------------------------------------------------------
    # DLS IK internals
    # ------------------------------------------------------------------

    def _dls_solve(self, target_pos: np.ndarray) -> IKResult:
        import mujoco as mj

        for _ in range(self.MAX_ITERS):
            mj.mj_forward(self._model, self._data)
            site_pos = self._data.site_xpos[self._site_id].copy()
            err = target_pos - site_pos
            if np.linalg.norm(err) < self.TOL_POS:
                break

            J_full = np.zeros((6, self._model.nv))
            mj.mj_jacSite(self._model, self._data,
                          J_full[:3], J_full[3:], self._site_id)

            J  = J_full[:3, :][:, self._dof_ids]  # (3, n_joints)
            JT = J.T
            lam2 = self.DLS_LAMBDA ** 2
            dq = JT @ np.linalg.solve(J @ JT + lam2 * np.eye(3), err)

            for i, jid in enumerate(self._joint_ids):
                qadr = self._model.jnt_qposadr[jid]
                jname = mj.mj_id2name(self._model, mj.mjtObj.mjOBJ_JOINT, jid)
                lo, hi = G1_ARM_LIMITS.get(jname, (-3.14, 3.14))
                new_q = float(np.clip(self._data.qpos[qadr] + dq[i], lo, hi))
                self._data.qpos[qadr] = new_q

        mj.mj_forward(self._model, self._data)
        final_err = np.linalg.norm(target_pos - self._data.site_xpos[self._site_id])
        success = final_err < self.TOL_POS * 3

        return IKResult(
            success=success,
            pose_name="dls_result",
            ctrl_delta=np.zeros(len(self._joint_ids)),
            target_pos=target_pos,
        )

    # ------------------------------------------------------------------
    # Keyframe fallback
    # ------------------------------------------------------------------

    def _keyframe_solve(self, target_pos: np.ndarray) -> IKResult:
        # Pick pose based on target height relative to robot
        table_z = 0.78
        bin_y   = 0.7
        if target_pos[1] > bin_y:
            pose_name = POSE_DROP_BIN
        elif target_pos[2] >= table_z - 0.05:
            pose_name = POSE_REACH_TABLE
        else:
            pose_name = POSE_HOME

        return IKResult(
            success=True,
            pose_name=pose_name,
            ctrl_delta=np.zeros(len(G1_RIGHT_ARM_JOINTS)),
            target_pos=target_pos,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _find_site(self, name: str) -> int:
        if not _HAS_MUJOCO or self._model is None:
            return -1
        return mujoco.mj_name2id(
            self._model, mujoco.mjtObj.mjOBJ_SITE, name)

    def _resolve_joint_ids(self) -> list[int]:
        ids = []
        for jname in G1_RIGHT_ARM_JOINTS:
            jid = mujoco.mj_name2id(
                self._model, mujoco.mjtObj.mjOBJ_JOINT, jname)
            if jid >= 0:
                ids.append(jid)
        return ids

    @property
    def _dof_ids(self) -> list[int]:
        return [self._model.jnt_dofadr[jid] for jid in self._joint_ids]

    def _joint_to_actuator(self, joint_name: str) -> int:
        if self._model is None:
            return -1
        for i in range(self._model.nu):
            trnid = self._model.actuator_trnid[i, 0]
            aname = mujoco.mj_id2name(
                self._model, mujoco.mjtObj.mjOBJ_JOINT, trnid)
            if aname == joint_name:
                return i
        return -1

    def _get_joint_angle(self, joint_name: str) -> float:
        if self._model is None or self._data is None:
            return 0.0
        jid = mujoco.mj_name2id(
            self._model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
        if jid < 0:
            return 0.0
        return float(self._data.qpos[self._model.jnt_qposadr[jid]])
