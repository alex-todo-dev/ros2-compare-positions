# Approach A — Hardcoded Joint Angles

## Status: DONE

## Description
Joint angles for each waypoint are manually defined by trial and error in simulation.
No kinematic model used — values are specific to this robot and task.

## Files
- `src/mycobot_ros2/mycobot_320/mycobot_320/mycobot_320/pick_place.py` — main script
- `src/mycobot_ros2/mycobot_320/mycobot_320/launch/gz_harmonic.launch.py` — Gazebo launch
- `src/mycobot_ros2/mycobot_320/mycobot_320/config/controllers.yaml` — ros2_control config
- `src/mycobot_ros2/mycobot_description/urdf/mycobot_320_m5_2022/mycobot_320_m5_2022_adaptive_gripper.urdf` — robot model
- `src/mycobot_ros2/mycobot_320/mycobot_320/worlds/mycobot_world.sdf` — Gazebo world
- `src/mycobot_ros2/mycobot_320/mycobot_320/models/cube/model.sdf` — cube object

## How to Run
```bash
# Terminal 1 — launch Gazebo + controllers
source /opt/ros/humble/setup.bash
source ~/Projects/mycobot_ws/install/setup.bash
ros2 launch mycobot_320 gz_harmonic.launch.py

# Terminal 2 — run pick and place
source /opt/ros/humble/setup.bash
source ~/Projects/mycobot_ws/install/setup.bash
ros2 run mycobot_320 pick_place

# Reset cube position if needed
gz service -s /world/mycobot_world/set_pose \
  --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 2000 \
  --req 'name: "cube", position: {x: 0.2620, y: -0.0842, z: 0.0300}, orientation: {x: 0, y: 0, z: 0.7071, w: 0.7071}'
```

## Waypoints (joint angles in radians)
| Waypoint | j1 | j2 | j3 | j4 | j5 | j6 |
|----------|----|----|----|----|----|-----|
| HOME | 0.0004 | 0.0042 | -0.0228 | 0.0045 | 0.0527 | 0.0077 |
| GRIPPER_READY | 0.0 | -0.0006 | -0.0856 | 0.0226 | 1.5567 | 0.0 |
| PRE_GRASP | 0.0 | -0.705 | -0.7237 | -0.1689 | 1.5772 | 0.0 |
| GRASP | 0.0 | -0.815 | -0.834 | -0.1689 | 1.5772 | 0.0 |

## Pros
- Simple to implement
- No dependencies beyond ROS2
- Deterministic and fast execution
- Easy to debug

## Cons
- Not portable — values are robot and task specific
- Brittle — breaks if cube position or robot model changes
- Must redo everything for a new target position
- No awareness of workspace or collisions

## Issues encountered
- Gripper briefly releases just before lift (fixed: re-assert GRIPPER_CLOSED before lift)
- Cube slides during grasp (open issue: gripper force / contact physics)

## Notes
- Gripper: OPEN=0.0, CLOSED=-1.0 via /gripper_action_controller/commands (Float64MultiArray)
- Arm: /arm_controller/joint_trajectory (JointTrajectory)
- Tolerance for "reached" check: 0.08 rad
