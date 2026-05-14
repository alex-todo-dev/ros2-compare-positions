"""
Pick-and-Place for mycobot_320 in Gazebo using Inverse Kinematics (ikpy).
Cartesian waypoints are solved to joint angles via the URDF kinematic chain.

Chain is truncated at link6 (excludes branching gripper joints).
Tool offset (link6 → grasp center) calibrated from Approach A known position.

Sequence: HOME → PRE_GRASP → GRASP → close gripper → LIFT → HOME (cube held).

Run:
    ros2 run pick_place_ik pick_place_ik
"""

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from std_msgs.msg import Float64MultiArray
from sensor_msgs.msg import JointState
from builtin_interfaces.msg import Duration as DurationMsg
from ament_index_python.packages import get_package_share_directory
import time
import os
import numpy as np

try:
    import ikpy.chain
except ImportError:
    raise SystemExit('ikpy not found. Install with: pip install ikpy')

ARM_JOINTS = [
    'joint2_to_joint1',
    'joint3_to_joint2',
    'joint4_to_joint3',
    'joint5_to_joint4',
    'joint6_to_joint5',
    'joint6output_to_joint6',
]

CUBE_X, CUBE_Y, CUBE_Z = 0.2620, -0.0842, 0.030

# Tool offset in link6 local frame (link6 origin → grasp center).
# Calibrated using Approach A GRASP joints as ground truth.
TOOL_OFFSET_LOCAL = [-0.0032, -0.0033, 0.144]

WAYPOINTS_CART = {
    'pre_grasp': np.array([CUBE_X, CUBE_Y, CUBE_Z + 0.09]),
    'grasp':     np.array([CUBE_X, CUBE_Y, CUBE_Z + 0.015]),
    'lift':      np.array([CUBE_X, CUBE_Y, CUBE_Z + 0.12]),
}

HOME_JOINTS = [0.0004, 0.0042, -0.0228, 0.0045, 0.0527, 0.0077]

# Approach A joints as IK seeds — ensures arm approaches from the correct side
SEED_PRE_GRASP = [0.0000, -0.7050, -0.7237, -0.1689, 1.5772, 0.0000]
SEED_GRASP     = [0.0000, -0.8150, -0.8340, -0.1689, 1.5772, 0.0000]

GRIPPER_OPEN   =  0.0
GRIPPER_CLOSED = -1.0

TOLERANCE = 0.05   # tighter — arm must truly be at target
TIMEOUT   = 20.0


def build_chain(urdf_path: str) -> tuple:
    """Build IK chain truncated at link6 with calibrated tool offset."""
    chain_full = ikpy.chain.Chain.from_urdf_file(
        urdf_path,
        base_elements=['world'],
        last_link_vector=TOOL_OFFSET_LOCAL,
    )
    stop_idx = next(i for i, l in enumerate(chain_full.links)
                    if l.name == 'joint6output_to_joint6')
    last_joint = chain_full.links[-1]
    arm_links = list(chain_full.links[:stop_idx + 1]) + [last_joint]
    chain = ikpy.chain.Chain(arm_links)

    arm_set = set(ARM_JOINTS)
    chain.active_links_mask = [l.name in arm_set for l in chain.links]
    arm_indices = [i for i, l in enumerate(chain.links) if l.name in arm_set]

    import rclpy.logging
    rclpy.logging.get_logger('ik_chain').info(f'Chain: {[l.name for l in chain.links]}')
    return chain, arm_indices


def ik_solve(chain, arm_indices, target_xyz, seed_joints):
    """Solve IK for a Cartesian target. joint6 forced to 0.0 to keep gripper perpendicular."""
    seed = np.zeros(len(chain.links))
    for idx, val in zip(arm_indices, seed_joints):
        seed[idx] = val
    result = chain.inverse_kinematics(
        target_position=target_xyz,
        initial_position=seed,
        orientation_mode=None,
    )
    joints = [result[i] for i in arm_indices]
    joints[-1] = 0.0
    return joints


class PickPlaceIK(Node):
    def __init__(self):
        super().__init__('pick_place_ik')

        urdf_path = os.path.join(
            get_package_share_directory('pick_place_ik'),
            'urdf', 'mycobot_320_m5_2022_adaptive_gripper.urdf'
        )
        self.get_logger().info(f'Loading URDF: {urdf_path}')
        self._chain, self._arm_indices = build_chain(urdf_path)

        self._arm = self.create_publisher(
            JointTrajectory, '/arm_controller/joint_trajectory', 10)
        self._gripper = self.create_publisher(
            Float64MultiArray, '/gripper_action_controller/commands', 10)

        self._joint_pos = {}
        self._joint_vel = {}
        self.create_subscription(JointState, '/joint_states', self._js_cb, 10)

    def _js_cb(self, msg):
        for name, pos, vel in zip(msg.name, msg.position, msg.velocity):
            self._joint_pos[name] = pos
            self._joint_vel[name] = vel

    def _ts(self):
        return f'[t={time.time():.2f}]'

    def run(self):
        self.get_logger().info('Waiting for joint states...')
        while not self._joint_pos:
            rclpy.spin_once(self, timeout_sec=0.1)
        self.get_logger().info('Joint states received — starting pick sequence.')
        self._pick_sequence()
        self.get_logger().info('Pick sequence complete.')

    def _pick_sequence(self):
        seeds = {
            'pre_grasp': SEED_PRE_GRASP,
            'grasp':     SEED_GRASP,
            'lift':      SEED_GRASP,
        }

        self._open_gripper()
        self._move_joints('home', HOME_JOINTS, sec=4)

        for name in ['pre_grasp', 'grasp', 'lift']:
            target = WAYPOINTS_CART[name]
            joints = ik_solve(self._chain, self._arm_indices, target, seeds[name])
            j_str = ', '.join(f'{v:.3f}' for v in joints)
            self.get_logger().info(
                f'{self._ts()} IK {name}: target={list(np.round(target, 4))} -> [{j_str}]'
            )

            if name == 'grasp':
                self._move_joints(name, joints, sec=5, dwell=2.0)
                self.get_logger().info(f'{self._ts()} ARM AT GRASP — starting gripper close')
                self._close_gripper(joints)
                self.get_logger().info(f'{self._ts()} GRIPPER CLOSE DONE — now lifting')
            elif name == 'lift':
                self._move_joints(name, joints, sec=3, dwell=0.5)
            else:
                self._move_joints(name, joints, sec=5, dwell=0.5)

        self._move_joints('home', HOME_JOINTS, sec=4)

    def _move_joints(self, name, positions, sec, dwell=0.5):
        self.get_logger().info(f'{self._ts()} Moving to: {name}')
        msg = JointTrajectory()
        msg.joint_names = ARM_JOINTS
        pt = JointTrajectoryPoint()
        pt.positions = [float(p) for p in positions]
        pt.time_from_start = DurationMsg(sec=sec, nanosec=0)
        msg.points = [pt]
        self._arm.publish(msg)

        deadline = time.time() + TIMEOUT
        while time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.05)
            if self._at_target(positions):
                self.get_logger().info(f'{self._ts()} Reached: {name} — dwell {dwell}s')
                self._pure_wait(dwell)
                return
        self.get_logger().warn(f'{self._ts()} Timeout reaching: {name} — continuing')

    def _at_target(self, target):
        if not self._joint_pos or not self._joint_vel:
            return False
        for joint, t in zip(ARM_JOINTS, target):
            if abs(self._joint_pos.get(joint, 99) - t) > TOLERANCE:
                return False
            if abs(self._joint_vel.get(joint, 99)) > 0.01:  # still moving
                return False
        return True

    def _close_gripper(self, arm_joints, duration=6.0):
        """Close gripper while holding arm fixed. Pure time.sleep — no spin calls."""
        t0 = time.time()

        # Single long-duration arm hold — controller commits with feedback
        arm_msg = JointTrajectory()
        arm_msg.joint_names = ARM_JOINTS
        pt = JointTrajectoryPoint()
        pt.positions = [float(p) for p in arm_joints]
        pt.time_from_start = DurationMsg(sec=30, nanosec=0)
        arm_msg.points = [pt]
        self._arm.publish(arm_msg)

        grip_msg = Float64MultiArray()
        grip_msg.data = [GRIPPER_CLOSED]
        count = 0
        while time.time() - t0 < duration:
            self._gripper.publish(grip_msg)
            count += 1
            time.sleep(0.1)

        self.get_logger().info(f'{self._ts()} Gripper close loop: {time.time()-t0:.1f}s, {count} commands')

    def _open_gripper(self):
        self.get_logger().info('Gripper: OPEN')
        grip_msg = Float64MultiArray()
        grip_msg.data = [GRIPPER_OPEN]
        deadline = time.time() + 2.0
        while time.time() < deadline:
            self._gripper.publish(grip_msg)
            rclpy.spin_once(self, timeout_sec=0.05)
            time.sleep(0.05)

    def _pure_wait(self, seconds):
        """Wait using only spin_once — no arm or gripper commands sent."""
        deadline = time.time() + seconds
        while time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.05)


def main(args=None):
    rclpy.init(args=args)
    node = PickPlaceIK()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
