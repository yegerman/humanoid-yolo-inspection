# Windows Unitree MuJoCo Demo

This folder separates the new Windows-specific Unitree MuJoCo demo workflow from the older mixed workspace files.

## What Was Added

- Windows-compatible Unitree DDS fixes in `external/unitree_sdk2_python`
- Windows-compatible Xbox XInput fallback in `external/unitree_mujoco/simulate_python`
- Two demo controllers in `external/unitree_mujoco/example/python`
  - `teleop_go2_demo.py` for Xbox controller
  - `teleop_go2_keyboard.py` for keyboard control

## Session Summary

This session completed the following work:

1. Installed and configured a Windows-capable toolchain for CycloneDDS.
2. Built CycloneDDS locally and installed it into `external/cyclonedds/install_vs`.
3. Created a Python 3.12 environment because CycloneDDS failed against Python 3.14.
4. Patched `unitree_sdk2_python` for Windows threading and CycloneDDS log-path compatibility.
5. Patched `unitree_mujoco` Python simulator for Windows interface selection and Xbox XInput fallback.
6. Added both gamepad and keyboard teleop scripts for the Go2 demo.
7. Calibrated idle teleop behavior so low-level commands follow the current robot pose with low gains instead of issuing walk commands while idle.

## Current Recommended Path

Use the keyboard teleop path first because it avoids controller drift entirely.

### Start Simulator

```powershell
Set-Location e:\huminoid\external\unitree_mujoco\simulate_python
$env:CYCLONEDDS_HOME='e:\huminoid\external\cyclonedds\install_vs'
$env:CMAKE_PREFIX_PATH='e:\huminoid\external\cyclonedds\install_vs'
e:\huminoid\.venv312\Scripts\python.exe unitree_mujoco.py
```

### Start Keyboard Teleop

```powershell
Set-Location e:\huminoid\external\unitree_mujoco\example\python
$env:CYCLONEDDS_HOME='e:\huminoid\external\cyclonedds\install_vs'
$env:CMAKE_PREFIX_PATH='e:\huminoid\external\cyclonedds\install_vs'
e:\huminoid\.venv312\Scripts\python.exe teleop_go2_keyboard.py
```

## Keyboard Controls

- `R`: stand and arm teleop
- `F`: sit
- `X`: freeze in current pose
- Hold `Space`: enable walking
- `W` / `S`: forward / back
- `A` / `D`: turn left / right
- Hold `Shift`: speed boost
- `Esc`: exit

## Files Changed

### Git-backed repo

- `external/unitree_sdk2_python/unitree_sdk2py/utils/thread.py`
- `external/unitree_sdk2_python/unitree_sdk2py/core/channel_config.py`

### Workspace files outside a git repo

- `external/unitree_mujoco/simulate_python/config.py`
- `external/unitree_mujoco/simulate_python/unitree_sdk2py_bridge.py`
- `external/unitree_mujoco/example/python/teleop_go2_demo.py`
- `external/unitree_mujoco/example/python/teleop_go2_keyboard.py`

## PR Note

Only `external/unitree_sdk2_python` is currently a git repo in this workspace for the Windows compatibility patches. The `external/unitree_mujoco` content in this workspace is not a git repo, so its changes cannot be included in the same GitHub PR from this machine without first turning that source tree into a git-backed checkout.