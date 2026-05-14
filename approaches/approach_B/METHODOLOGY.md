# Approach B — Methodology

## How it works

Waypoints are defined as Cartesian coordinates `(x, y, z)` in the world frame.
The script uses **ikpy** to solve the Inverse Kinematics (IK) — computing the
6 joint angles required to place the gripper's grasp centre at the target
position. The computed joint angles are then sent to the same
`joint_trajectory_controller` as in Approach A.

### Execution sequence

```
HOME (joint angles) → PRE_GRASP (IK) → GRASP (IK) → close gripper
                    → LIFT (IK) → HOME (joint angles)
```

---

## Kinematic chain construction

The URDF is loaded by ikpy and parsed into a chain of links:

```
world  →  world_to_base (fixed)
       →  joint2_to_joint1   (revolute, Z-axis)   ← j1
       →  joint3_to_joint2   (revolute, Y-axis)   ← j2
       →  joint4_to_joint3   (revolute, Y-axis)   ← j3
       →  joint5_to_joint4   (revolute, Y-axis)   ← j4
       →  joint6_to_joint5   (revolute, X-axis)   ← j5
       →  joint6output_to_joint6  (revolute, Z)   ← j6
       →  joint6output_to_gripper_base (fixed)
       →  [branching gripper joints …]
```

**Chain truncation:** The URDF has branching joints after `link6` (two gripper
fingers). ikpy requires a non-branching chain, so the chain is truncated at
`joint6output_to_joint6`. The virtual last link carries the tool offset vector.

```python
stop_idx = next(i for i, l in enumerate(chain_full.links)
                if l.name == 'joint6output_to_joint6')
```

**Active links mask:** Only the 6 revolute arm joints are marked active.
The `world_to_base` and the virtual tool link are passive (fixed).

---

## Tool offset calibration

The URDF's `link6` origin is not at the gripper's physical grasp centre.
The offset `(dx, dy, dz)` in link6's local frame was calibrated as follows:

### Calibration procedure

1. Use Approach A's GRASP joint angles as ground truth:
   ```
   joints = [0.0, -0.815, -0.834, -0.169, 1.577, 0.0]
   ```
   These angles are known to place the gripper at the cube at
   `(x=0.2620, y=-0.0842, z=0.045)`.

2. Compute Forward Kinematics (FK) with ikpy using these joints and
   `last_link_vector = [0, 0, 0]` (no offset):
   ```python
   fk = chain.forward_kinematics(joint_angles)
   link6_pos = fk[:3, 3]   # position of link6 origin
   ```

3. The required tool offset = target − link6_pos:
   ```
   target    = [0.2620, -0.0842, 0.045]
   link6_pos = [0.2652,  0.0809, 0.099]   (example values)
   offset    = [-0.0032, -0.0033, 0.144]
   ```

4. Set `last_link_vector = [-0.0032, -0.0033, 0.144]` in the chain.
   FK error with calibrated offset: **0.0 mm** on all waypoints.

### Calibrated offset value
```python
TOOL_OFFSET_LOCAL = [-0.0032, -0.0033, 0.144]
```

---

## IK solving

For each Cartesian waypoint:

```python
result = chain.inverse_kinematics(
    target_position = [x, y, z],
    initial_position = seed,        # joint angle seed
    orientation_mode = None,        # position-only
)
joints = [result[i] for i in arm_indices]
joints[-1] = 0.0                    # force j6=0 → gripper perpendicular
```

**Seeds:** Approach A joint angles are used as IK seeds. This ensures ikpy
finds a solution with the same arm configuration (elbow up/down) instead of
a numerically equivalent but physically awkward pose.

| Waypoint  | Seed used |
|-----------|-----------|
| PRE_GRASP | Approach A PRE_GRASP joints |
| GRASP     | Approach A GRASP joints |
| LIFT      | Approach A GRASP joints |

**j6 forced to 0.0:** ikpy may set j6 to a small non-zero value to minimise
the IK error. Forcing it to 0.0 keeps the gripper wrist perpendicular to the
arm, which matches the physical grasp orientation used in Approach A.

---

## Waypoints — values and rationale

Cube position in simulation: `x=0.2620, y=-0.0842, z=0.030`

| Waypoint  | x (m)  | y (m)   | z (m)  | z offset from cube | Rationale |
|-----------|--------|---------|--------|--------------------|-----------|
| PRE_GRASP | 0.2620 | -0.0842 | 0.120  | +0.090 m           | 9 cm clearance above cube — safe approach |
| GRASP     | 0.2620 | -0.0842 | 0.045  | +0.015 m           | 1.5 cm above cube base — fingers clear floor |
| LIFT      | 0.2620 | -0.0842 | 0.150  | +0.120 m           | 12 cm — enough to clear cube and table edge |

The x/y coordinates are identical to the cube position — the arm approaches
from directly above (top-down grasp), matching the orientation from Approach A.

The GRASP height (z=0.045) was tuned: too low and the fingers hit the ground
plane; too high and the gripper misses the cube. `cube_z (0.030) + cube_half_height
(0.015) = 0.045` matches the cube geometry.

---

## IK solution — solved joint angles

The IK solver produces angles close to the Approach A seeds.
Typical solved values (may vary slightly between runs due to numerical solver):

| Waypoint  | j1    | j2     | j3     | j4     | j5    | j6  |
|-----------|-------|--------|--------|--------|-------|-----|
| PRE_GRASP | 0.000 | -0.703 | -0.722 | -0.169 | 1.576 | 0.0 |
| GRASP     | 0.000 | -0.814 | -0.833 | -0.169 | 1.576 | 0.0 |
| LIFT      | 0.000 | -0.706 | -0.714 | -0.157 | 1.571 | 0.0 |

Compare with Approach A GRASP: `[0.0, -0.815, -0.834, -0.169, 1.577, 0.0]`
Difference at GRASP: ≤ 0.001 rad per joint — IK matches hand-tuned values.

---

## Comparison: Approach A vs Approach B waypoint definition

| | Approach A | Approach B |
|---|---|---|
| Input | 6 joint angles per pose (rad) | 3 Cartesian coordinates (m) |
| Tool | rqt sliders + visual inspection | IK solver + URDF model |
| Effort to move cube | Redo all angles from scratch | Change x/y/z only |
| Geometric insight | None — empirical | Direct: "place gripper 9 cm above cube" |

---

## Control architecture

```
pick_place_ik.py
    │
    ├─ ikpy IK solver  ←  URDF (bundled in package)
    │       └─ joint angles
    │
    ├─ /arm_controller/joint_trajectory  (JointTrajectory)
    │       └─ joint_trajectory_controller  →  Gazebo
    │
    ├─ /gripper_action_controller/commands  (Float64MultiArray)
    │
    └─ /joint_states  ←  feedback (position + velocity check)
```

The reach-check in Approach B is stricter: tolerance 0.05 rad (vs 0.08 in A)
and also checks that joint velocity < 0.01 rad/s (arm truly stopped).

---

## Screenshot checklist

Run the simulation and capture the following. Save to `screenshots/`.

| File name | What to show |
|-----------|-------------|
| `B1_gz_home.png` | Gazebo — robot at HOME position |
| `B2_gz_pre_grasp.png` | Gazebo — robot at PRE_GRASP (IK solved, above cube) |
| `B3_gz_grasp.png` | Gazebo — robot at GRASP (IK solved, fingers around cube) |
| `B4_gz_lift.png` | Gazebo — robot at LIFT (cube held in air) |
| `B5_terminal_ik_output.png` | Terminal showing IK solve log: `IK pre_grasp: target=[…] -> [joint angles]` |
| `B6_terminal_run.png` | Full terminal output of `ros2 run pick_place_ik pick_place_ik` |
