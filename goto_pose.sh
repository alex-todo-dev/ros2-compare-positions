#!/bin/bash
# Move robot to a named pose for screenshots.
# Usage: ./goto_pose.sh <pose_name>
# Poses: home | gripper_ready | pre_grasp | grasp | lift

source /opt/ros/humble/setup.bash
source ~/Projects/mycobot_ws/install/setup.bash

case "$1" in
  home)
    JOINTS="[0.0004, 0.0042, -0.0228, 0.0045, 0.0527, 0.0077]"
    ;;
  gripper_ready)
    JOINTS="[0.0, -0.0006, -0.0856, 0.0226, 1.5567, 0.0]"
    ;;
  pre_grasp)
    JOINTS="[0.0, -0.705, -0.7237, -0.1689, 1.5772, 0.0]"
    ;;
  grasp)
    JOINTS="[0.0, -0.815, -0.834, -0.1689, 1.577, 0.0]"
    ;;
  lift)
    JOINTS="[0.0, -0.705, -0.7237, -0.1689, 1.5772, 0.0]"
    ;;
  *)
    echo "Usage: $0 <home|gripper_ready|pre_grasp|grasp|lift>"
    exit 1
    ;;
esac

NAMES="['joint2_to_joint1','joint3_to_joint2','joint4_to_joint3','joint5_to_joint4','joint6_to_joint5','joint6output_to_joint6']"

ros2 topic pub --once /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory \
  "{joint_names: ${NAMES}, points: [{positions: ${JOINTS}, time_from_start: {sec: 3, nanosec: 0}}]}"

echo "Moving to: $1"
