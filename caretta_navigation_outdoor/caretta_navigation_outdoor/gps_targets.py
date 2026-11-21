"""Test targets for GPS goals: an X on the ground in RViz with its latitude/longitude below it.

Type the shown latitude/longitude into the RViz "GpsGoal" panel and press Go. The lat/lon comes
from navsat_transform (/toLL), so it is exactly what the robot uses.
  ros2 run caretta_navigation_outdoor gps_targets --ros-args -p use_sim_time:=true
  own points (map x, y in m): -p points:="[2.5, 0.0, 5.0, 0.0, 10.0, 3.0]"
  out: /gps_targets (visualization_msgs/MarkerArray, every 2 s)
"""
from geometry_msgs.msg import Point
import rclpy
from rclpy.node import Node
from robot_localization.srv import ToLL
from visualization_msgs.msg import Marker, MarkerArray

# default, both on the gravel path: T1 (yellow) 10.6 m along the south side (picked at random),
# T2 (red) 5 m in front of the robot's start (spawn (0, 0) facing east, +x)
DEFAULT_POINTS = [10.6, 0.0, 5.0, 0.0]
X_SIZE = 0.4          # m, half length of the X arms
COLOURS = [(0.95, 0.66, 0.23), (0.85, 0.15, 0.15), (0.15, 0.45, 0.85), (0.60, 0.20, 0.70)]


class GpsTargets(Node):

    def __init__(self):
        super().__init__('gps_targets')
        flat = self.declare_parameter('points', DEFAULT_POINTS).value
        self.points = list(zip(flat[0::2], flat[1::2]))
        self.lat_lon = [None] * len(self.points)
        self.to_ll = self.create_client(ToLL, 'toLL')
        self.pub = self.create_publisher(MarkerArray, '/gps_targets', 1)
        self.create_timer(2.0, self.tick)

    def tick(self):
        # ask navsat_transform once for every point, then keep publishing the markers
        if not all(self.lat_lon):
            if not self.to_ll.service_is_ready():
                self.get_logger().info('waiting for /toLL (navsat_transform) ...', throttle_duration_sec=5.0)
                return
            for i, (x, y) in enumerate(self.points):
                if self.lat_lon[i] is None:
                    req = ToLL.Request()
                    req.map_point = Point(x=float(x), y=float(y), z=0.0)
                    self.to_ll.call_async(req).add_done_callback(lambda f, i=i: self.on_ll(i, f))
            return
        self.pub.publish(self.markers())

    def on_ll(self, i, future):
        ll = future.result().ll_point
        # navsat_transform answers 0, 0 until it has its transform (first GPS fix + datum): ask again
        if ll.latitude == 0.0 and ll.longitude == 0.0:
            return
        self.lat_lon[i] = (ll.latitude, ll.longitude)
        x, y = self.points[i]
        self.get_logger().info(
            f'T{i + 1}: map ({x:+.2f}, {y:+.2f}) -> lat {ll.latitude:.7f}, lon {ll.longitude:.7f}')

    def markers(self):
        out = MarkerArray()
        stamp = self.get_clock().now().to_msg()
        for i, ((x, y), (lat, lon)) in enumerate(zip(self.points, self.lat_lon)):
            r, g, b = COLOURS[i % len(COLOURS)]
            cross = Marker()
            cross.header.frame_id = 'map'
            cross.header.stamp = stamp
            cross.ns = 'gps_target_x'
            cross.id = i
            cross.type = Marker.LINE_LIST
            cross.scale.x = 0.08                      # line width
            cross.color.r, cross.color.g, cross.color.b, cross.color.a = r, g, b, 1.0
            cross.pose.orientation.w = 1.0
            z = 0.02
            cross.points = [Point(x=x - X_SIZE, y=y - X_SIZE, z=z), Point(x=x + X_SIZE, y=y + X_SIZE, z=z),
                            Point(x=x - X_SIZE, y=y + X_SIZE, z=z), Point(x=x + X_SIZE, y=y - X_SIZE, z=z)]
            out.markers.append(cross)

            label = Marker()
            label.header = cross.header
            label.ns = 'gps_target_label'
            label.id = i
            label.type = Marker.TEXT_VIEW_FACING
            label.pose.position.x = x
            label.pose.position.y = y - X_SIZE - 0.55   # below the X in the top-down view (south)
            label.pose.position.z = 0.1
            label.pose.orientation.w = 1.0
            label.scale.z = 0.22                       # text height, m
            label.color.r = label.color.g = label.color.b = label.color.a = 1.0
            label.text = f'T{i + 1}\nlat {lat:.7f}\nlon {lon:.7f}'
            out.markers.append(label)
        return out


def main():
    rclpy.init()
    node = GpsTargets()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
