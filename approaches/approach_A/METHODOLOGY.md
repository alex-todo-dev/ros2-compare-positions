# Approach A — Methodology

## How it works

The robot is programmed by directly specifying joint angles (in radians) for each
pose. No kinematic model is used. The controller receives a `JointTrajectory`
message with the target angles and a duration; the `joint_trajectory_controller`
interpolates from the current position to the target over that duration.

The gripper is controlled separately via a `Float64MultiArray` message on
`/gripper_action_controller/commands`: `0.0` = open, `-1.0` = fully closed.

### Execution sequence

```
HOME → GRIPPER_READY → PRE_GRASP → GRASP → close gripper
     → hold GRASP → LIFT (PRE_GRASP) → HOME
```

After each move the script reads `/joint_states` and waits until all 6 joints
are within 0.08 rad of the target before proceeding. If the arm does not reach
the target within 20 s the script logs a warning and continues.

---

## How positions were chosen — rqt method

The waypoints were found interactively using **rqt_joint_trajectory_controller**:

1. Launch Gazebo with the robot loaded:
   ```bash
   ros2 launch approach_a gz_harmonic.launch.py
   ```

2. Open rqt and load the Joint Trajectory Controller plugin:
   ```bash
   rqt
   # Plugins → Robot Tools → Joint Trajectory Controller
   # Controller manager ns: /controller_manager
   # Controller: arm_controller  →  Enable
   ```
   Six sliders appear, one per joint (`joint2_to_joint1` … `joint6output_to_joint6`).

3. Move each slider while watching Gazebo. Adjust until the gripper is visually
   at the desired position (above the cube, level with the cube, etc.).

4. Read the current joint angles from the `/joint_states` topic:
   ```bash
   ros2 topic echo /joint_states --once
   ```

5. Copy the `position` array into the script as the waypoint.

6. Run the script, observe the motion, and refine values iteratively.

### Iterations required per waypoint

| Waypoint      | Iterations | Main adjustment |
|---------------|-----------|-----------------|
| HOME          | 1         | Near-zero angles — start position |
| GRIPPER_READY | 2         | j5 set to π/2 so gripper points down |
| PRE_GRASP     | 4         | j2/j3 tuned to land 9 cm above cube |
| GRASP         | 6         | j2/j3 lowered until gripper contacts cube; j4 corrects tilt |

---

## Waypoints — values and rationale

### Joint naming convention
```
joint2_to_joint1  = j1  (base rotation — yaw)
joint3_to_joint2  = j2  (shoulder pitch)
joint4_to_joint3  = j3  (elbow pitch)
joint5_to_joint4  = j4  (wrist pitch)
joint6_to_joint5  = j5  (wrist roll)
joint6output_to_joint6 = j6 (end-effector rotation)
```

### HOME  `[0.0004, 0.0042, −0.0228, 0.0045, 0.0527, 0.0077]`
All values near zero. The robot stands upright. This is the controller's
default after the spawn-and-home sequence at launch. Slight non-zero values
reflect the equilibrium of the physical (simulated) joints.

### GRIPPER_READY  `[0.0, −0.0006, −0.0856, 0.0226, 1.5567, 0.0]`
j5 ≈ π/2 (1.5567 rad). This rotates the wrist so the gripper fingers point
straight down — a prerequisite for a top-down grasp. j2/j3 keep the arm
near-vertical while j5 rotates the end-effector.

### PRE_GRASP  `[0.0, −0.705, −0.724, −0.169, 1.577, 0.0]`
The gripper is positioned approximately 9 cm above the cube centre.
- j2 and j3 together extend the arm forward and downward toward the cube.
- j4 compensates for the compound pitch of j2+j3 to keep the gripper level.
- j5 stays at π/2 to maintain the top-down orientation.

Approximate end-effector height above table: ~0.120 m
Cube centre height: 0.030 m → clearance ≈ 0.090 m ✓

### GRASP  `[0.0, −0.815, −0.834, −0.169, 1.577, 0.0]`
j2 and j3 each reduced by ~0.11 rad vs PRE_GRASP, lowering the gripper
until the fingers straddle the cube (gripper contact height ≈ 0.045 m).
j4 unchanged — the lowering is symmetric in j2/j3 so the pitch compensation
does not change.

---

## Control architecture

```
pick_place.py
    │
    ├─ /arm_controller/joint_trajectory  (JointTrajectory)
    │       └─ joint_trajectory_controller  →  Gazebo joint effort
    │
    ├─ /gripper_action_controller/commands  (Float64MultiArray)
    │       └─ JointGroupPositionController  →  gripper_controller joint
    │
    └─ /joint_states  (JointState)  ← feedback for reach-check
```

Controller update rate: 100 Hz (set in `controllers.yaml`).
State publish rate: 50 Hz.

---

## Known issues and fixes

| Issue | Cause | Fix applied |
|-------|-------|-------------|
| Gripper releases just before lift | Gripper command not re-asserted after arm move | `GRIPPER_CLOSED` re-sent before lift move |
| Cube slides during lift | Gripper contact physics — simulated friction | Gripper re-asserted twice with 0.3 s dwell |

---

## Screenshot checklist

Run the simulation and capture the following. Save to `screenshots/`.

| File name | What to show |
|-----------|-------------|
| `A1_rqt_sliders.png` | rqt Joint Trajectory Controller panel with sliders |
| `A2_rqt_joint_states.png` | rqt topic monitor showing `/joint_states` output |
| `A3_gz_home.png` | Gazebo — robot at HOME position |
| `A4_gz_pre_grasp.png` | Gazebo — robot at PRE_GRASP (above cube) |
| `A5_gz_grasp.png` | Gazebo — robot at GRASP (fingers around cube) |
| `A6_gz_lift.png` | Gazebo — robot at LIFT (cube held in air) |
| `A7_terminal_run.png` | Terminal showing `ros2 run approach_a pick_place` output |
