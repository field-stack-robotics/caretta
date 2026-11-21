"""Caretta control: controllers + twist_mux. Same file for Gazebo and the real robot.

Start it once the controller_manager is up (Gazebo: after the robot is spawned).
  ros2 launch caretta_control control.launch.py use_sim_time:=true

Velocity input (twist_mux, see config/twist_mux.yaml):
  /cmd_vel_teleop  teleop, priority 100
  /cmd_vel         Nav2,   priority 10
  /e_stop          std_msgs/Bool, true stops everything
  -> /diff_drive_controller/cmd_vel_unstamped
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    control_share = get_package_share_directory('caretta_control')
    twist_mux_config = os.path.join(control_share, 'config', 'twist_mux.yaml')
    use_sim_time = LaunchConfiguration('use_sim_time')

    # one spawner for both controllers (configured in config/caretta_controllers.yaml)
    controllers = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', 'diff_drive_controller',
                   '--controller-manager-timeout', '30'],
        output='screen',
    )

    twist_mux = Node(
        package='twist_mux',
        executable='twist_mux',
        parameters=[twist_mux_config, {'use_sim_time': use_sim_time}],
        remappings=[('/cmd_vel_out', '/diff_drive_controller/cmd_vel_unstamped')],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false',
                              description='true in Gazebo (use the /clock topic)'),
        controllers,
        twist_mux,
    ])
