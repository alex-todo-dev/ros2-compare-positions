import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import FindExecutable, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = get_package_share_directory('pick_place_ik')

    urdf_file = os.path.join(pkg_share, 'urdf', 'mycobot_320_m5_2022_adaptive_gripper.urdf')
    controllers_file = os.path.join(pkg_share, 'config', 'controllers.yaml')
    world_file = os.path.join(pkg_share, 'worlds', 'mycobot_world_ik.sdf')
    cube_sdf_file = os.path.join(pkg_share, 'models', 'cube', 'model.sdf')

    # Make meshes in the description package visible to Gazebo
    mycobot_desc_share = get_package_share_directory('mycobot_description')
    os.environ['GZ_SIM_RESOURCE_PATH'] = os.path.dirname(mycobot_desc_share)

    with open(urdf_file, 'r') as f:
        robot_desc = f.read()
    # Replace the controllers.yaml placeholder with our local copy
    robot_desc = robot_desc.replace(
        '$(find mycobot_320)/config/controllers.yaml', controllers_file
    )

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py'])
        ]),
        launch_arguments=[('gz_args', ['-r -v 1 ', world_file])]
    )

    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_desc, 'use_sim_time': True}]
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'mycobot_320',
            '-x', '0.0', '-y', '0.0', '-z', '-0.01',
        ]
    )

    spawn_cube = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=['-file', cube_sdf_file, '-name', 'cube',
                   '-x', '0.2620', '-y', '-0.0842', '-z', '0.0300', '-Y', '1.5708']
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/world/mycobot_world/pose/info@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
        ],
        output='screen'
    )

    load_jsb = Node(
        package='controller_manager', executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        output='screen'
    )
    load_arm = Node(
        package='controller_manager', executable='spawner',
        arguments=['arm_controller', '--controller-manager', '/controller_manager'],
        output='screen'
    )
    load_gripper = Node(
        package='controller_manager', executable='spawner',
        arguments=['gripper_action_controller', '--controller-manager', '/controller_manager'],
        output='screen'
    )

    after_spawn = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_robot,
            on_exit=[spawn_cube, load_jsb]
        )
    )
    after_jsb = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=load_jsb,
            on_exit=[load_arm, load_gripper]
        )
    )

    set_home = ExecuteProcess(
        cmd=[FindExecutable(name='ros2'), 'run', 'pick_place_ik', 'set_home_pose'],
        output='screen'
    )

    after_arm = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=load_arm,
            on_exit=[set_home]
        )
    )

    return LaunchDescription([gz_sim, bridge, rsp, spawn_robot, after_spawn, after_jsb, after_arm])
