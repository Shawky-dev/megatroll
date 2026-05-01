import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command

def generate_launch_description():
    urdf_path = os.path.join(
        get_package_share_directory('megajaw_description'),
        'urdf',
        'megajaw.xacro.urdf'
    )

    robot_description_content = Command(['xacro ', urdf_path])

    # Publishes TF from your URDF
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_content,
                     'use_sim_time': False}]
    )

    # Loads your hardware plugin (MegaJawHardware)
    controller_manager = Node(
        package='controller_manager',
        executable='ros2_control_node',
        output='screen',
        parameters=[{'robot_description': robot_description_content}]
    )

    return LaunchDescription([
        robot_state_publisher,
        controller_manager,
    ])
