"""Caretta GPS localization: dual-antenna heading + navsat_transform + global EKF -> map -> odom.

  ros2 launch caretta_navigation_outdoor gps_localization.launch.py use_sim_time:=true

Needs: Gazebo with world:=caretta_outdoor gps:=true (GPS topics, local EKF from caretta_localization).
Outputs: /odometry/global (robot in map), /odometry/gps, /gps/filtered, /gps/heading, TF map -> odom
         and the service /fromLL (lat/lon -> map), used by the GPS waypoint script.
Settings: config/gps_localization.yaml
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory('caretta_navigation_outdoor')
    config = os.path.join(share, 'config', 'gps_localization.yaml')
    use_sim_time = LaunchConfiguration('use_sim_time')

    # heading from the two antennas -> /gps/heading
    heading = Node(
        package='caretta_navigation_outdoor',
        executable='dual_gps_heading',
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    # global EKF: publishes map -> odom; its output is renamed so it does not clash with the local EKF
    ekf_global = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_global',
        parameters=[config, {'use_sim_time': use_sim_time}],
        remappings=[('odometry/filtered', 'odometry/global')],
        output='screen',
    )

    # GPS lat/lon -> x, y in the map frame (uses the rear antenna, its offset comes from TF)
    navsat = Node(
        package='robot_localization',
        executable='navsat_transform_node',
        name='navsat_transform',
        parameters=[config, {'use_sim_time': use_sim_time}],
        remappings=[('imu', 'gps/heading'),
                    ('gps/fix', 'gps/rear/fix'),
                    ('odometry/filtered', 'odometry/global')],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false',
                              description='true in Gazebo (use the /clock topic)'),
        heading,
        ekf_global,
        navsat,
    ])
