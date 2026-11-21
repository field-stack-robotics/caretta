"""Caretta local localization: robot_localization EKF (wheel odometry + IMU).

  ros2 launch caretta_localization localization.launch.py use_sim_time:=true

Inputs:  /diff_drive_controller/odom (vx, vy, vyaw), /imu (vyaw)   see config/ekf.yaml
Outputs: /odometry/filtered and the TF odom -> caretta_base_footprint
The diff_drive_controller must not publish that TF too (enable_odom_tf: false).
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    localization_share = get_package_share_directory('caretta_localization')
    ekf_config = os.path.join(localization_share, 'config', 'ekf.yaml')
    use_sim_time = LaunchConfiguration('use_sim_time')

    # name must match the top key in config/ekf.yaml, or the node silently uses defaults
    ekf = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        parameters=[ekf_config, {'use_sim_time': use_sim_time}],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false',
                              description='true in Gazebo (use the /clock topic)'),
        ekf,
    ])
