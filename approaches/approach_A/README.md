# Approach A — Hardcoded Joint Angles

Pick-and-place on mycobot 320 M5 using manually tuned joint angles.

## Prerequisites

- Ubuntu 22.04
- ROS2 Humble — [install guide](https://docs.ros.org/en/humble/Installation.html)
- Gazebo Harmonic (gz-sim 8.x)
- ROS2 packages: `ros_gz_sim`, `ros_gz_bridge`, `ros2_control`, `joint_trajectory_controller`

```bash
sudo apt install ros-humble-ros-gz ros-humble-ros2-control \
     ros-humble-joint-trajectory-controller \
     ros-humble-joint-state-broadcaster \
     ros-humble-position-controllers
```

## Setup

```bash
mkdir -p ~/ws/src
cd ~/ws/src
# place this folder here so the path is ~/ws/src/approach_A/
cd ~/ws
colcon build --packages-select approach_a
source install/setup.bash
```

## Run

```bash
# Terminal 1 — Gazebo + controllers
source /opt/ros/humble/setup.bash && source ~/ws/install/setup.bash
ros2 launch approach_a gz_harmonic.launch.py

# Terminal 2 — pick-and-place script
source /opt/ros/humble/setup.bash && source ~/ws/install/setup.bash
ros2 run approach_a pick_place
```

## Reset cube position

```bash
gz service -s /world/mycobot_world/set_pose \
  --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 2000 \
  --req 'name: "cube", position: {x: 0.2620, y: -0.0842, z: 0.0300}, orientation: {x: 0, y: 0, z: 0.7071, w: 0.7071}'
```

## Waypoints (joint angles in radians)

| Waypoint      | j1     | j2      | j3      | j4      | j5     | j6     |
|---------------|--------|---------|---------|---------|--------|--------|
| HOME          | 0.0004 | 0.0042  | −0.0228 | 0.0045  | 0.0527 | 0.0077 |
| GRIPPER_READY | 0.0    | −0.0006 | −0.0856 | 0.0226  | 1.5567 | 0.0    |
| PRE_GRASP     | 0.0    | −0.7050 | −0.7237 | −0.1689 | 1.5772 | 0.0    |
| GRASP         | 0.0    | −0.8150 | −0.8340 | −0.1689 | 1.5772 | 0.0    |
