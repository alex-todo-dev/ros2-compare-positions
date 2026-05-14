# Approach C — MoveIt2 Motion Planning

## Status: PLANNED

## Description
Use MoveIt2 to plan and execute pick-and-place. MoveIt2 handles IK, collision
avoidance, and path planning. Targets defined as Cartesian poses.
Requires creating a dedicated MoveIt2 config package from scratch.

## Files
All files live in their own package — nothing shared with other approaches.

- `src/pick_place_moveit/pick_place_moveit/pick_place_moveit.py` — main script (to create)
- `src/pick_place_moveit/launch/gz_harmonic_moveit.launch.py` — own copy of Gazebo launch (to create)
- `src/pick_place_moveit/launch/move_group.launch.py` — MoveIt2 move_group launch (to create)
- `src/pick_place_moveit/config/controllers.yaml` — own copy of controllers config (to create)
- `src/pick_place_moveit/config/mycobot_320.srdf` — MoveIt2 semantic robot description (to create)
- `src/pick_place_moveit/config/joint_limits.yaml` — joint limits for MoveIt2 (to create)
- `src/pick_place_moveit/config/kinematics.yaml` — IK solver config for MoveIt2 (to create)
- `src/pick_place_moveit/urdf/mycobot_320_m5_2022_adaptive_gripper.urdf` — own copy of URDF (to copy)
- `src/pick_place_moveit/worlds/mycobot_world_moveit.sdf` — own copy of world (to create)
- `src/pick_place_moveit/models/cube/model.sdf` — own copy of cube model (to copy)
- `src/pick_place_moveit/package.xml`
- `src/pick_place_moveit/setup.py`

## How to Run
```bash
# Terminal 1 — launch Gazebo + controllers
source /opt/ros/humble/setup.bash
source ~/Projects/mycobot_ws/install/setup.bash
ros2 launch pick_place_moveit gz_harmonic_moveit.launch.py

# Terminal 2 — launch MoveIt2 move_group
source /opt/ros/humble/setup.bash
source ~/Projects/mycobot_ws/install/setup.bash
ros2 launch pick_place_moveit move_group.launch.py

# Terminal 3 — run pick and place
source /opt/ros/humble/setup.bash
source ~/Projects/mycobot_ws/install/setup.bash
ros2 run pick_place_moveit pick_place_moveit

# Reset cube position if needed
gz service -s /world/mycobot_world/set_pose \
  --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 2000 \
  --req 'name: "cube", position: {x: 0.2620, y: -0.0842, z: 0.0300}, orientation: {x: 0, y: 0, z: 0.7071, w: 0.7071}'
```

## Pros
- Collision-aware path planning
- Industry standard approach
- Handles singularities and joint limits automatically
- Easy to add obstacles to planning scene

## Cons
- Heaviest setup — MoveIt2 config package required
- Adds latency (planning time varies)
- Most complex to configure of all approaches
- Requires 3 terminals (Gazebo + move_group + script)

## Progress Log
- [ ] Create pick_place_moveit package structure
- [ ] Copy and adapt URDF, world, controllers
- [ ] Run MoveIt Setup Assistant to generate SRDF + config files
- [ ] Test move_group launching alongside Gazebo
- [ ] Implement pick_place_moveit.py
- [ ] Compare results against A and B
