"""
Pick-and-Place for mycobot_320 in Gazebo.
Verifies each step by reading joint states before proceeding.

Run:
    ros2 run mycobot_320 pick_place
"""

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from std_msgs.msg import Float64MultiArray
from sensor_msgs.msg import JointState
from builtin_interfaces.msg import Duration as DurationMsg
import time
import math

ARM_JOINTS = [
    'joint2_to_joint1',
    'joint3_to_joint2',
    'joint4_to_joint3',
    'joint5_to_joint4',
    'joint6_to_joint5',
    'joint6output_to_joint6',
]

HOME          = [+0.0004, +0.0042, -0.0228, +0.0045, +0.0527, +0.0077]
GRIPPER_READY = [+0.0000, -0.0006, -0.0856, +0.0226, +1.5567, +0.0000]
PRE_GRASP     = [+0.0000, -0.7050, -0.7237, -0.1689, +1.5772, +0.0000]
GRASP         = [+0.0000, -0.8150, -0.8340, -0.1689, +1.5772, +0.0000]

GRIPPER_OPEN   =  0.0
GRIPPER_CLOSED = -1.0

TOLERANCE  = 0.08   # rad — accepted as "reached"
TIMEOUT    = 20.0   # seconds max wait per step


class PickPlace(Node):
    def __init__(self):
        super().__init__('pick_place')

        self._arm = self.create_publisher(
            JointTrajectory, '/arm_controller/joint_trajectory', 10)
        self._gripper = self.create_publisher(
            Float64MultiArray, '/gripper_action_controller/commands', 10)

        self._joint_pos = {}
        self.create_subscription(JointState, '/joint_states', self._js_cb, 10)

        self.get_logger().info('Waiting for joint states...')
        self.create_timer(1.0, self._run_once)
        self._started = False

    def _js_cb(self, msg):
        for name, pos in zip(msg.name, msg.position):
            self._joint_pos[name] = pos

    def _run_once(self):
        if self._started or not self._joint_pos:
            return
        self._started = True
        self._pick()
        self.get_logger().info('Done.')

    def _pick(self):
        self._grip(GRIPPER_OPEN)
        self._move('home',          HOME,          sec=4)
        self._move('gripper_ready', GRIPPER_READY, sec=4)
        self._move('pre_grasp',     PRE_GRASP,     sec=4)
        self._move('grasp',         GRASP,         sec=5)
        self._grip(GRIPPER_CLOSED)
        self._move('grasp',         GRASP,         sec=2)  # re-hold position after gripper closes
        self._wait(1.0)
        self._grip(GRIPPER_CLOSED)  # re-assert grip immediately before lift
        self._wait(0.3)
        self._move('pre_grasp',     PRE_GRASP,     sec=5)
        self._move('home',          HOME,          sec=6)

    # ------------------------------------------------------------------

    def _move(self, name, positions, sec):
        self.get_logger().info(f'Moving to: {name}')
        msg = JointTrajectory()
        msg.joint_names = ARM_JOINTS
        pt = JointTrajectoryPoint()
        pt.positions = [float(p) for p in positions]
        pt.time_from_start = DurationMsg(sec=sec, nanosec=0)
        msg.points = [pt]
        self._arm.publish(msg)

        # Wait until arm actually reaches target
        deadline = time.time() + TIMEOUT
        while time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.05)
            if self._at_target(positions):
                self.get_logger().info(f'Reached: {name}')
                self._wait(2.0)  # settle before next move
                return
        self.get_logger().warn(f'Timeout reaching: {name} — continuing anyway')

    def _at_target(self, target):
        if not self._joint_pos:
            return False
        for joint, t in zip(ARM_JOINTS, target):
            current = self._joint_pos.get(joint)
            if current is None:
                return False
            if abs(current - t) > TOLERANCE:
                return False
        return True

    def _grip(self, position):
        label = 'OPEN' if position >= 0.0 else 'CLOSE'
        self.get_logger().info(f'Gripper: {label} ({position})')
        msg = Float64MultiArray()
        msg.data = [position]
        self._gripper.publish(msg)
        rclpy.spin_once(self, timeout_sec=0.1)

    def _wait(self, seconds):
        deadline = time.time() + seconds
        while time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.05)


def main(args=None):
    rclpy.init(args=args)
    node = PickPlace()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
