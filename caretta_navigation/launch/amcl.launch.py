"""Caretta localization on a saved map: map_server + AMCL (Nav2).

  ros2 launch caretta_navigation amcl.launch.py use_sim_time:=true      (RViz; rviz:=false to skip)
  other map: map:=/path/to/map.yaml   (default: maps/caretta_house.yaml)

Inputs:  the map, /scan and the TF odom -> caretta_base_footprint (EKF, caretta_localization)
Outputs: /map, /particle_cloud, /amcl_pose and the TF map -> odom
Do NOT run together with slam.launch.py: both publish map -> odom.
Wrong start pose? Set it in RViz with "2D Pose Estimate".
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
    amcl_config = os.path.join(navigation_share, 'config', 'amcl.yaml')
    default_map = os.path.join(navigation_share, 'maps', 'caretta_house.yaml')
    rviz_config = os.path.join(navigation_share, 'rviz', 'amcl.rviz')
    use_sim_time = LaunchConfiguration('use_sim_time')

    # loads the .yaml + .pgm and publishes /map
    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        parameters=[{'yaml_filename': LaunchConfiguration('map'),
                     'use_sim_time': use_sim_time}],
        output='screen',
    )

    # particle filter: name must match the top key in config/amcl.yaml
    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        parameters=[amcl_config, {'use_sim_time': use_sim_time}],
        output='screen',
    )

    # Nav2 nodes are lifecycle nodes: this starts them, in order (map first, then AMCL)
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        parameters=[{'use_sim_time': use_sim_time,
                     'autostart': True,
                     'node_names': ['map_server', 'amcl']}],
        output='screen',
    )

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
        DeclareLaunchArgument('map', default_value=default_map,
                              description='map yaml file (from map_saver_cli)'),
        DeclareLaunchArgument('rviz', default_value='true', description='start RViz with the map'),
        map_server,
        amcl,
        lifecycle_manager,
        rviz,
    ])
