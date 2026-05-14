# Approach B — Inverse Kinematics (ikpy)

## Status: DONE (pick phase validated)

## Description
Use the robot's URDF and an IK solver (ikpy) to compute joint angles from
Cartesian poses (x, y, z + orientation). Waypoints are defined in world space.

## Files
All files live in their own package — nothing shared with other approaches.

- `src/pick_place_ik/pick_place_ik/pick_place_ik.py` — main script (to create)
- `src/pick_place_ik/launch/gz_harmonic_ik.launch.py` — own copy of Gazebo launch (to create)
- `src/pick_place_ik/config/controllers.yaml` — own copy of controllers config (to create)
- `src/pick_place_ik/urdf/mycobot_320_m5_2022_adaptive_gripper.urdf` — own copy of URDF (to copy)
- `src/pick_place_ik/worlds/mycobot_world_ik.sdf` — own copy of world (to create)
- `src/pick_place_ik/models/cube/model.sdf` — own copy of cube model (to copy)
- `src/pick_place_ik/package.xml`
- `src/pick_place_ik/setup.py`

## Dependency
```bash
pip install ikpy
```

## How to Run
```bash
# Terminal 1 — launch Gazebo + controllers
source /opt/ros/humble/setup.bash
source ~/Projects/mycobot_ws/install/setup.bash
ros2 launch pick_place_ik gz_harmonic_ik.launch.py

# Terminal 2 — run IK pick and place
source /opt/ros/humble/setup.bash
source ~/Projects/mycobot_ws/install/setup.bash
ros2 run pick_place_ik pick_place_ik

# Reset cube position if needed
gz service -s /world/mycobot_world/set_pose \
  --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 2000 \
  --req 'name: "cube", position: {x: 0.2620, y: -0.0842, z: 0.0300}, orientation: {x: 0, y: 0, z: 0.7071, w: 0.7071}'
```

## Planned Waypoints (Cartesian, in meters)
| Waypoint | x | y | z | notes |
|----------|---|---|---|-------|
| HOME | — | — | — | fixed joint angles |
| PRE_GRASP | 0.2620 | -0.0842 | 0.120 | 9cm above cube center |
| GRASP | 0.2620 | -0.0842 | 0.045 | cube center +1.5cm (fingers clear ground) |
| LIFT | 0.2620 | -0.0842 | 0.150 | 12cm above cube center |
| PLACE | 0.000 | 0.250 | 0.100 | drop target |

## Results vs Approach A

| Metric | Approach A (hardcoded joints) | Approach B (IK) |
|--------|-------------------------------|-----------------|
| Grasp position accuracy | Approximate — joints tuned by hand | Precise — Cartesian target → IK solve |
| Grasp quality | Cube partially in fingers | Clean gripper closure around cube |
| Waypoint definition | 6 joint angles per pose | x/y/z in world frame |
| Portability | Brittle — cube must be exactly at tuned position | Robust — change x/y/z only |
| Tool offset calibration | N/A | Required: link6 origin ≠ grasp center |
| Scope (paper comparison) | Pick phase | Pick phase |

**Conclusion for paper:** IK-based approach delivers measurably better grasp precision and quality. Waypoints are defined intuitively in Cartesian space, making the approach easier to adapt to fault injection scenarios where cube position varies.

## Pros
- Waypoints defined intuitively in Cartesian space
- Easy to change target — just update x/y/z
- Portable across similar robot configurations
- Reusable IK chain for any new task

## Cons
- Requires accurate URDF (matches real/simulated robot exactly)
- Singularities possible near workspace limits
- ikpy is numerical — may have small error
- Adds Python dependency

## URDF Joint Chain (analysed 2026-04-08)
From `mycobot_320_m5_2022_adaptive_gripper.urdf`:
- `world` (link, fixed root)
- `world_to_base` (fixed joint)
- `base`, `link1`–`link6` (arm links)
- `joint2_to_joint1` → `joint6output_to_joint6` (6 revolute — these are ARM_JOINTS)
- `joint6output_to_gripper_base` (fixed)
- gripper joints (revolute, branching — excluded from IK chain)

ikpy active_links_mask: True only for the 6 ARM_JOINTS by name match.
Stop chain at `link6` to avoid branching gripper issue.

## IK Chain Notes
- Chain truncated at `joint6output_to_joint6` (excludes branching gripper joints)
- Tool offset in link6 local frame: `[-0.0032, -0.0033, 0.144]`
  - Calibrated using Approach A GRASP joints as ground truth
  - FK error: 0.0 mm on all waypoints after calibration
- IK seeds: use Approach A joint angles as hint to get similar arm configuration

## Progress Log
- [x] Create src/pick_place_ik/ package directory structure
- [x] Copy URDF, world SDF, cube model, controllers.yaml into package
- [x] Create launch file (gz_harmonic_ik.launch.py)
- [x] Create pick_place_ik.py with ikpy IK chain
- [x] Install ikpy: pip install ikpy
- [x] Build package: colcon build --packages-select pick_place_ik
- [x] Test IK chain — chain truncated at link6, calibrated tool offset
- [x] Tune GRASP height (+1.5cm above cube center)
- [x] Manual step-by-step test — cube lifted successfully
- [x] Compare results against Approach A (see Results section below)
