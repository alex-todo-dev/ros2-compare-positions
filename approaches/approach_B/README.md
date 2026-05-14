# Approach B — Inverse Kinematics (ikpy)

Pick-and-place on mycobot 320 M5 using Cartesian waypoints + ikpy IK solver.

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

pip install ikpy
```

## Setup

```bash
mkdir -p ~/ws/src
cd ~/ws/src
# place this folder here so the path is ~/ws/src/approach_B/
cd ~/ws
colcon build --packages-select pick_place_ik
source install/setup.bash
```

## Run

```bash
# Terminal 1 — Gazebo + controllers
source /opt/ros/humble/setup.bash && source ~/ws/install/setup.bash
ros2 launch pick_place_ik gz_harmonic_ik.launch.py

# Terminal 2 — IK pick-and-place script
source /opt/ros/humble/setup.bash && source ~/ws/install/setup.bash
ros2 run pick_place_ik pick_place_ik
```

## Reset cube position

```bash
gz service -s /world/mycobot_world/set_pose \
  --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 2000 \
  --req 'name: "cube", position: {x: 0.2620, y: -0.0842, z: 0.0300}, orientation: {x: 0, y: 0, z: 0.7071, w: 0.7071}'
```

## Waypoints (Cartesian, meters)

| Waypoint  | x     | y      | z     | Description         |
|-----------|-------|--------|-------|---------------------|
| PRE_GRASP | 0.262 | −0.084 | 0.120 | 9 cm above cube     |
| GRASP     | 0.262 | −0.084 | 0.045 | grasp height        |
| LIFT      | 0.262 | −0.084 | 0.150 | 12 cm above cube    |
| PLACE     | 0.000 | 0.250  | 0.100 | drop target         |
