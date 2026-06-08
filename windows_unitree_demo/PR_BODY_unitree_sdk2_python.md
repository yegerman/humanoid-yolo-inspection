# PR: Add Windows support for recurrent threads and DDS logging

## Summary

This PR adds the minimum Windows compatibility changes needed for the Python Unitree SDK integration used by the local MuJoCo demo.

## Changes

- make recurrent thread scheduling work on Windows without `timerfd`
- fix the zero-interval recurrent thread helper argument path
- replace the Linux-only CycloneDDS log path with a portable local filename

## Why

The upstream code path assumes Linux-only primitives and paths.
On Windows this caused:

- thread helper failures because `timerfd` is unavailable
- CycloneDDS config issues because `/tmp/cdds.LOG` is not a valid default path

## Validation

- local Windows runtime used successfully with Python 3.12
- the patched SDK was exercised with the MuJoCo simulator bridge
- the branch is committed cleanly as `4b51cbd`

## Out Of Scope

The related simulator bridge, XInput fallback, and teleop demo scripts live in the workspace copy of `external/unitree_mujoco`, which is not a git repo in this checkout and therefore are not included in this PR.

## Suggested PR Command

```powershell
Set-Location e:\huminoid\external\unitree_sdk2_python
git push -u origin windows-dds-fixes
gh pr create --title "Add Windows support for recurrent threads and DDS logging" --body-file e:\huminoid\windows_unitree_demo\PR_BODY_unitree_sdk2_python.md
```
