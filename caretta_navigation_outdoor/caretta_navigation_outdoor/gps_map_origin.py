"""Publish the map origin (navsat_transform datum) as a NavSatFix in the map frame.

rviz_satellite (AerialMap display) puts the satellite tiles around a NavSatFix, in that message's
frame. The antenna fixes turn with the robot, so the tiles would turn too; this fixed origin in the
map frame lines the tiles up with map (x east, y north).
  out: /gps/map_origin (sensor_msgs/NavSatFix, 1 Hz)
Keep latitude/longitude equal to the navsat_transform datum (config/gps_localization.yaml).
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, NavSatStatus


class GpsMapOrigin(Node):

    def __init__(self):
        super().__init__('gps_map_origin')
        self.fix = NavSatFix()
        self.fix.header.frame_id = self.declare_parameter('frame_id', 'map').value
        self.fix.latitude = self.declare_parameter('latitude', 52.0).value
        self.fix.longitude = self.declare_parameter('longitude', 5.0).value
        self.fix.altitude = 0.0
        self.fix.status.status = NavSatStatus.STATUS_FIX
        self.fix.position_covariance_type = NavSatFix.COVARIANCE_TYPE_UNKNOWN
        self.pub = self.create_publisher(NavSatFix, '/gps/map_origin', 1)
        self.create_timer(1.0, self.publish)

    def publish(self):
        self.fix.header.stamp = self.get_clock().now().to_msg()
        self.pub.publish(self.fix)


def main():
    rclpy.init()
    node = GpsMapOrigin()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
