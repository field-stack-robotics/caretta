"""Caretta outdoor navigation with GPS: GPS localization + Nav2 without a map + RViz.

  ros2 launch caretta_gazebo gazebo.launch.py world:=caretta_outdoor gps:=true
  ros2 launch caretta_navigation_outdoor gps_navigation.launch.py use_sim_time:=true
  ros2 run caretta_navigation_outdoor gps_waypoints --ros-args -p use_sim_time:=true

Goals: RViz "GpsGoal" panel (type lat/lon, Go), RViz "2D Goal Pose" (map = Gazebo world: x east,
y north), or GPS waypoints (gps_waypoints).
RViz ground: the top-down image of the Gazebo world (outdoor_ground), lined up with the simulation.
Real satellite tiles (rviz_satellite, Esri, internet) are in the "Satellite" display, off by default:
the Gazebo world is made up, so they do not match it (useful on a real field).
Teleop (/cmd_vel_teleop) wins over Nav2, /e_stop stops both (twist_mux, caretta_control).
Indoor navigation (caretta_navigation) is separate; do not run both.
Settings: config/gps_localization.yaml, config/nav2_outdoor.yaml
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
    share = get_package_share_directory('caretta_navigation_outdoor')
    nav2_config = os.path.join(share, 'config', 'nav2_outdoor.yaml')
    rviz_config = os.path.join(share, 'rviz', 'gps_navigation.rviz')
    gps_launch = os.path.join(share, 'launch', 'gps_localization.launch.py')
    nav2_launch = os.path.join(get_package_share_directory('nav2_bringup'),
                               'launch', 'navigation_launch.py')
    use_sim_time = LaunchConfiguration('use_sim_time')

    # where am I: dual-antenna heading + navsat_transform + global EKF (map -> odom).
    # GroupAction keeps the include's launch arguments from leaking into this file.
    gps = GroupAction([IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gps_launch),
        launch_arguments={'use_sim_time': use_sim_time}.items(),
    )])

    # how do I get there: Nav2 with a rolling global costmap (no map outdoors)
    nav2 = GroupAction([IncludeLaunchDescription(
        PythonLaunchDescriptionSource(nav2_launch),
        launch_arguments={'use_sim_time': use_sim_time,
                          'params_file': nav2_config,
                          'autostart': 'true'}.items(),
    )])

    # GPS goals typed in the RViz "GpsGoal" panel (caretta_rviz_plugins) -> /fromLL -> Nav2
    gps_goal = Node(
        package='caretta_navigation_outdoor',
        executable='gps_goal',
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    # test targets: an X on the ground with its lat/lon (T1 2.5 m, T2 5 m in front of the start)
    targets = Node(
        package='caretta_navigation_outdoor',
        executable='gps_targets',
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(LaunchConfiguration('rviz')),
        output='screen',
    )

    # map origin as a NavSatFix in the map frame: lines up the satellite tiles in RViz
    map_origin = Node(
        package='caretta_navigation_outdoor',
        executable='gps_map_origin',
        parameters=[os.path.join(share, 'config', 'gps_localization.yaml'),
                    {'use_sim_time': use_sim_time}],
        condition=IfCondition(LaunchConfiguration('rviz')),
        output='screen',
    )

    # top-down image of the Gazebo world as the ground in RViz (lines up with the simulation)
    ground = Node(
        package='caretta_navigation_outdoor',
        executable='outdoor_ground',
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(LaunchConfiguration('rviz')),
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
        DeclareLaunchArgument('rviz', default_value='true', description='start RViz'),
        gps,
        nav2,
        gps_goal,
        targets,
        map_origin,
        ground,
        rviz,
    ])
