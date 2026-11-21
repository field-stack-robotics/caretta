"""Caretta navigation: AMCL on the saved map + Nav2 (go to a goal on its own).

  ros2 launch caretta_navigation navigation.launch.py use_sim_time:=true   (RViz; rviz:=false to skip)
  other map: map:=/path/to/map.yaml   (default: maps/caretta_house.yaml)

Give a goal in RViz with "2D Goal Pose". Keyboard teleop (/cmd_vel_teleop) always wins over Nav2
(/cmd_vel) in twist_mux, and /e_stop stops both.
Starts amcl.launch.py itself: do NOT run it together with amcl.launch.py or slam.launch.py.
Settings: config/nav2.yaml (Nav2), config/amcl.yaml (AMCL)
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    navigation_share = get_package_share_directory('caretta_navigation')
    nav2_config = os.path.join(navigation_share, 'config', 'nav2.yaml')
    default_map = os.path.join(navigation_share, 'maps', 'caretta_house.yaml')
    rviz_config = os.path.join(navigation_share, 'rviz', 'navigation.rviz')
    amcl_launch = os.path.join(navigation_share, 'launch', 'amcl.launch.py')
    nav2_launch = os.path.join(get_package_share_directory('nav2_bringup'),
                               'launch', 'navigation_launch.py')
    use_sim_time = LaunchConfiguration('use_sim_time')

    # where am I: map_server + AMCL (RViz is started below, not there).
    # GroupAction scopes the include: without it, its rviz:=false leaks out and turns off our RViz.
    amcl = GroupAction([IncludeLaunchDescription(
        PythonLaunchDescriptionSource(amcl_launch),
        launch_arguments={'use_sim_time': use_sim_time,
                          'map': LaunchConfiguration('map'),
                          'rviz': 'false'}.items(),
    )])

    # how do I get there: planner, controller, costmaps, behavior tree, recoveries (our nav2.yaml)
    nav2 = GroupAction([IncludeLaunchDescription(
        PythonLaunchDescriptionSource(nav2_launch),
        launch_arguments={'use_sim_time': use_sim_time,
                          'params_file': nav2_config,
                          'autostart': 'true'}.items(),
    )])

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
        DeclareLaunchArgument('rviz', default_value='true', description='start RViz'),
        amcl,
        nav2,
        rviz,
    ])
