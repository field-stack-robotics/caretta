"""Drive Caretta through GPS waypoints (latitude, longitude) with Nav2.

Each waypoint is turned into map coordinates by navsat_transform (/fromLL service), then the
list goes to Nav2's waypoint follower. Default: one lap of the gravel path in caretta_outdoor.sdf
(corners WP2 -> WP3 -> WP4 -> WP1, counter-clockwise, back to the start).

  ros2 run caretta_navigation_outdoor gps_waypoints --ros-args -p use_sim_time:=true
  own points: -p waypoints:="[52.0, 5.0002, 52.0001, 5.0002]"   (lat, lon, lat, lon, ...)
"""
import math

from geographic_msgs.msg import GeoPoint
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import rclpy
from robot_localization.srv import FromLL

# path corners of caretta_outdoor.sdf (world origin lat 52.0, lon 5.0; 30 m east, 20 m north)
DEFAULT_WAYPOINTS = [
    52.000000, 5.000437,   # (30, 0)  south-east corner (WP2)
    52.000180, 5.000437,   # (30, 20) north-east corner (WP3)
    52.000180, 5.000000,   # (0, 20)  north-west corner (WP4)
    52.000000, 5.000000,   # (0, 0)   start, south-west corner (WP1)
]


def main():
    rclpy.init()
    nav = BasicNavigator()
    flat = nav.declare_parameter('waypoints', DEFAULT_WAYPOINTS).value
    lat_lon = list(zip(flat[0::2], flat[1::2]))

    # localization is robot_localization (not a lifecycle node), so wait for a Nav2 server instead
    nav.waitUntilNav2Active(localizer='controller_server')

    from_ll = nav.create_client(FromLL, 'fromLL')
    while not from_ll.wait_for_service(timeout_sec=2.0):
        nav.info('waiting for /fromLL (navsat_transform) ...')

    points = []
    for lat, lon in lat_lon:
        req = FromLL.Request()
        req.ll_point = GeoPoint(latitude=lat, longitude=lon, altitude=0.0)
        future = from_ll.call_async(req)
        rclpy.spin_until_future_complete(nav, future)
        p = future.result().map_point
        points.append((p.x, p.y))
        nav.info(f'lat {lat:.6f}, lon {lon:.6f} -> map ({p.x:+.2f}, {p.y:+.2f})')

    poses = []
    for i, (x, y) in enumerate(points):
        # face the next waypoint (the last one keeps the direction it arrived from)
        if i + 1 < len(points):
            nx, ny = points[i + 1]
        else:
            nx, ny = 2 * x - points[i - 1][0], 2 * y - points[i - 1][1]
        yaw = math.atan2(ny - y, nx - x)
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = nav.get_clock().now().to_msg()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)
        poses.append(pose)

    nav.followWaypoints(poses)
    last = -1
    while not nav.isTaskComplete():
        feedback = nav.getFeedback()
        if feedback and feedback.current_waypoint != last:
            last = feedback.current_waypoint
            nav.info(f'going to waypoint {last + 1} of {len(poses)}')

    # the waypoint follower skips a waypoint it cannot reach (stop_on_failure: false) and still
    # ends with SUCCEEDED, so check the missed ones too
    result = nav.getResult()
    missed = list(nav.result_future.result().result.missed_waypoints)
    if result == TaskResult.SUCCEEDED and not missed:
        nav.info(f'all {len(poses)} waypoints reached')
    else:
        nav.warn(f'result {result}, missed waypoints (1 = first): {[i + 1 for i in missed]}')
    nav.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
