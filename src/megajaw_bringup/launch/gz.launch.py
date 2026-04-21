import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    urdf_path = os.path.join(get_package_share_directory('megajaw_description'), 'urdf', 'megajaw.xacro.urdf')
    world_file_path = os.path.join(get_package_share_directory('megajaw_bringup'), 'worlds', 'my_world.sdf')
    
    # Launch Arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default=True)
    
    ld = LaunchDescription()
    
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': Command(['xacro ', urdf_path])}],
        output='screen',
    )
    
    gz_spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=['-topic', 'robot_description', '-name',
                   'diff_drive', '-allow_renaming', 'true'],
    )
    
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster'],
    )
    
    # Controller
    # robot_controllers = PathJoinSubstitution(
    #     [
    #         FindPackageShare('gz_ros2_control_demos'),
    #         'config',
    #         'diff_drive_controller.yaml',
    #     ]
    # )


    # diff_drive_base_controller_spawner = Node(
    #     package='controller_manager',
    #     executable='spawner',
    #     arguments=[
    #         'diff_drive_base_controller',
    #         '--param-file',
    #         robot_controllers,
    #         '--controller-ros-args',
    #         '-r /diff_drive_controller/cmd_vel:=/cmd_vel',
    #     ],
    # )

    
    # Bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen'
    )

    ld = LaunchDescription([
        # Launch gazebo environment
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [PathJoinSubstitution([FindPackageShare('ros_gz_sim'),
                                       'launch',
                                       'gz_sim.launch.py'])]),
            launch_arguments=[('gz_args', [' -r -v 1 ', world_file_path])]),
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=gz_spawn_entity,
                on_exit=[joint_state_broadcaster_spawner],
            )
        ),
        # RegisterEventHandler(
        #     event_handler=OnProcessExit(
        #         target_action=joint_state_broadcaster_spawner,
        #         on_exit=[diff_drive_base_controller_spawner],
        #     )
        # ),
        bridge,
        gz_spawn_entity,
        robot_state_publisher,
        
        # Launch Arguments
        DeclareLaunchArgument(
            'use_sim_time',
            default_value=use_sim_time,
            description='If true, use simulated clock'),
        DeclareLaunchArgument(
            'description_format',
            default_value='urdf',
            description='Robot description format to use, urdf or sdf'),
    ])
    
    return ld
    