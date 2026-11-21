"""Caretta SLAM: build a map with the LiDAR (slam_toolbox, online async).

  ros2 launch caretta_navigation slam.launch.py use_sim_time:=true      (RViz with the map; rviz:=false to skip)

Save the map (while SLAM runs), from the workspace root:
  ros2 run nav2_map_server map_saver_cli -f src/caretta/caretta_navigation/maps/<name> \
    --ros-args -p use_sim_time:=true

Inputs:  /scan and the TF odom -> caretta_base_footprint (EKF, caretta_localization)
Outputs: /map (occupancy grid) and the TF map -> odom
Settings: config/slam_toolbox.yaml
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    navigation_share = get_package_share_directory('caretta_navigation')
    slam_config = os.path.join(navigation_share, 'config', 'slam_toolbox.yaml')
    rviz_config = os.path.join(navigation_share, 'rviz', 'slam.rviz')
    use_sim_time = LaunchConfiguration('use_sim_time')

    # async: skips scans it cannot keep up with, always works on the newest one.
    # name must match the top key in config/slam_toolbox.yaml
    slam = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        parameters=[slam_config, {'use_sim_time': use_sim_time}],
        output='screen',
    )

    # Fixed Frame map + Map display (/map, Transient Local)
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(LaunchConfiguration('rviz')),
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false',
                              description='true in Gazebo (use the /clock topic)'),
        DeclareLaunchArgument('rviz', default_value='true', description='start RViz with the map'),
        slam,
        rviz,
    ])
