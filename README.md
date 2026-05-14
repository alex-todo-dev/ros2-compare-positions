# ros2-compare-positions

Comparison of pick-and-place programming approaches for the **mycobot_320 M5** robot arm in ROS2 / Gazebo Harmonic simulation.

| Approach | Method | Package |
|----------|--------|---------|
| **A** | Hardcoded joint angles (manual rqt calibration) | `approach_a` |
| **B** | Inverse Kinematics via ikpy (Cartesian waypoints) | `pick_place_ik` |

Full academic report (English and Bulgarian) with screenshots, videos, calculations and code analysis:
- `report_en.html` / `report_en.pdf`
- `report_bg.html` / `report_bg.pdf`

---

## Requirements

- Ubuntu 22.04
- ROS2 Humble
- Gazebo Harmonic (gz-sim 8)
- Python 3.10

---

## 1. Install ROS2 Humble

```bash
# Set locale
sudo apt update && sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8

# Add ROS2 apt repository
sudo apt install -y software-properties-common curl
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list

# Install ROS2 Humble desktop
sudo apt update && sudo apt install -y ros-humble-desktop

# Add to .bashrc
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

---

## 2. Install Gazebo Harmonic and ROS-Gazebo Bridge

```bash
# Add Gazebo apt repository
sudo curl https://packages.osrfoundation.org/gazebo.gpg \
  --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] \
  http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/gazebo-stable.list

sudo apt update && sudo apt install -y gz-harmonic

# ROS2 ↔ Gazebo bridge and simulation packages
sudo apt install -y \
  ros-humble-ros-gz-sim \
  ros-humble-ros-gz-bridge \
  ros-humble-ros-gz-interfaces
```

---

## 3. Install ros2_control

```bash
sudo apt install -y \
  ros-humble-ros2-control \
  ros-humble-ros2-controllers \
  ros-humble-gz-ros2-control
```

---

## 4. Install mycobot_description (robot URDF/meshes)

```bash
sudo apt install -y ros-humble-mycobot-description
# or clone into your workspace src/ if not available via apt:
# git clone https://github.com/elephantrobotics/mycobot_ros2.git src/mycobot_ros2
```

---

## 5. Clone and Build This Repository

```bash
# Clone
git clone https://github.com/alex-todo-dev/ros2-compare-positions.git
cd ros2-compare-positions

# Create symlinks so colcon can find the packages
ln -s $(pwd)/approaches/approach_A src/approach_a
ln -s $(pwd)/approaches/approach_B src/pick_place_ik

# Install Python dependency for Approach B
pip install ikpy

# Build
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

---

## 6. Run Approach A — Hardcoded Joint Angles

**Terminal 1** — launch simulation:
```bash
source /opt/ros/humble/setup.bash && source install/setup.bash
ros2 launch approach_a gz_harmonic.launch.py
```

Wait for Gazebo to open and the arm to move to the home position (~10 seconds).

**Terminal 2** — run pick-and-place:
```bash
source /opt/ros/humble/setup.bash && source install/setup.bash
ros2 run approach_a pick_place
```

The arm will execute: HOME → GRIPPER_READY → PRE_GRASP → GRASP → close gripper → LIFT → HOME

---

## 7. Run Approach B — Inverse Kinematics

**Terminal 1** — launch simulation:
```bash
source /opt/ros/humble/setup.bash && source install/setup.bash
ros2 launch pick_place_ik gz_harmonic_ik.launch.py
```

Wait for Gazebo to open and the arm to move to the home position (~10 seconds).

**Terminal 2** — run pick-and-place:
```bash
source /opt/ros/humble/setup.bash && source install/setup.bash
ros2 run pick_place_ik pick_place_ik
```

The arm will execute: HOME → PRE_GRASP (IK) → GRASP (IK) → close gripper → LIFT (IK) → HOME

---

## 8. Reset Simulation Between Runs

To reset the cube to its starting position without restarting Gazebo:
```bash
gz service -s /world/mycobot_world/set_pose \
  --reqtype gz.msgs.Pose \
  --reptype gz.msgs.Boolean \
  --timeout 2000 \
  --req 'name: "cube", position: {x: 0.262, y: -0.0842, z: 0.03}'
```

To move the arm back to home manually:
```bash
source /opt/ros/humble/setup.bash && source install/setup.bash
ros2 topic pub -1 /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory \
  "{joint_names: ['joint2_to_joint1','joint3_to_joint2','joint4_to_joint3','joint5_to_joint4','joint6_to_joint5','joint6output_to_joint6'], \
    points: [{positions: [0.0004, 0.0042, -0.0228, 0.0045, 0.0527, 0.0077], time_from_start: {sec: 4, nanosec: 0}}]}"
```

---

## Repository Structure

```
ros2-compare-positions/
├── approaches/
│   ├── approach_A/          # Approach A ROS2 package (approach_a)
│   │   ├── approach_a/      # Python source (pick_place.py, set_home_pose.py)
│   │   ├── launch/          # gz_harmonic.launch.py
│   │   ├── config/          # controllers.yaml
│   │   ├── urdf/            # robot URDF
│   │   ├── worlds/          # Gazebo world SDF
│   │   ├── models/cube/     # cube model SDF
│   │   └── screenshots/     # screenshots and video
│   └── approach_B/          # Approach B ROS2 package (pick_place_ik)
│       ├── pick_place_ik/   # Python source (pick_place_ik.py, set_home_pose.py)
│       ├── launch/          # gz_harmonic_ik.launch.py
│       ├── config/          # controllers.yaml
│       ├── urdf/            # robot URDF
│       ├── worlds/          # Gazebo world SDF
│       ├── models/cube/     # cube model SDF
│       └── screenshots/     # screenshots and video
├── report_en.html           # Full English report (open in browser)
├── report_en.pdf            # Full English report (PDF)
├── report_bg.html           # Full Bulgarian report (open in browser)
├── report_bg.pdf            # Full Bulgarian report (PDF)
└── goto_pose.sh             # Helper: move arm to named pose
```

---

## Tested Environment

| Component | Version |
|-----------|---------|
| Ubuntu | 22.04 LTS |
| ROS2 | Humble Hawksbill |
| Gazebo | Harmonic (gz-sim 8) |
| Python | 3.10 |
| ikpy | 3.3+ |
