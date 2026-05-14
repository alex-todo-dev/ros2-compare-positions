#!/usr/bin/env python3
"""
Send a single JointTrajectory command to move the arm to the home position.
Runs once then exits — called at launch time after arm_controller is ready.
"""

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
import time

HOME = [0.0004, 0.0042, -0.0228, 0.0045, 0.0527, 0.0077]

JOINTS = [
    'joint2_to_joint1',
    'joint3_to_joint2',
    'joint4_to_joint3',
    'joint5_to_joint4',
    'joint6_to_joint5',
    'joint6output_to_joint6',
]


def main():
    rclpy.init()
    node = Node('set_home_pose')

    pub = node.create_publisher(JointTrajectory, '/arm_controller/joint_trajectory', 10)

    time.sleep(5.0)

    while pub.get_subscription_count() == 0:
        time.sleep(0.5)

    msg = JointTrajectory()
    msg.joint_names = JOINTS

    point = JointTrajectoryPoint()
    point.positions = HOME
    point.time_from_start = Duration(sec=3, nanosec=0)
    msg.points = [point]

    pub.publish(msg)
    node.get_logger().info(f'Home pose sent: {HOME}')

    time.sleep(0.5)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
