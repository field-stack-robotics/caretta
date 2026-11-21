"""Caretta outdoor navigation with GPS: GPS localization + Nav2 without a map + RViz.

  ros2 launch caretta_gazebo gazebo.launch.py world:=caretta_outdoor gps:=true
  ros2 launch caretta_navigation_outdoor gps_navigation.launch.py use_sim_time:=true
  ros2 run caretta_navigation_outdoor gps_waypoints --ros-args -p use_sim_time:=true

Goals: RViz "GpsGoal" panel (type lat/lon, Go), RViz "2D Goal Pose" (map = Gazebo world: x east,
y north), or GPS waypoints (gps_waypoints).
RViz ground: the top-down image of the Gazebo world as map tiles (media/ground_tiles, drawn behind
the costmaps by rviz_satellite), lined up with the simulation.
Real satellite tiles (rviz_satellite, Esri, internet) are in the "Satellite" display, off by default:
the Gazebo world is made up, so they do not match it (useful on a real field).
Teleop (/cmd_vel_teleop) wins over Nav2, /e_stop stops both (twist_mux, caretta_control).
Indoor navigation (caretta_navigation) is separate; do not run both.
Settings: config/gps_localization.yaml, config/nav2_outdoor.yaml
"""
import os
import tempfile

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
    # the RViz config loads the Gazebo ground tiles from this package with a file:// URL;
    # the absolute path is only known here, so write a copy of the config with it filled in
    with open(os.path.join(share, 'rviz', 'gps_navigation.rviz')) as f:
        rviz_text = f.read().replace('@GROUND_TILES@', os.path.join(share, 'media', 'ground_tiles'))
    rviz_config = os.path.join(tempfile.gettempdir(), 'caretta_gps_navigation.rviz')
    with open(rviz_config, 'w') as f:
        f.write(rviz_text)
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

    # test targets on the path: an X on the ground with its lat/lon (T1 at 10.6 m, T2 at 5 m, south side)
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
        rviz,
    ])
