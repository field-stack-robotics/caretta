"""Heading from a dual-antenna RTK GPS (like a u-blox ZED-F9P moving base).

The two antennas sit on the robot's x axis (rear -> front), so the direction of the line between
them is the robot heading. Publishes it as sensor_msgs/Imu (orientation only) for robot_localization.
  in:  /gps/rear/fix, /gps/front/fix   (sensor_msgs/NavSatFix)
  out: /gps/heading                   (sensor_msgs/Imu, yaw in ENU: east = 0, counter-clockwise +)

  ros2 run caretta_navigation_outdoor dual_gps_heading --ros-args -p use_sim_time:=true

On the real robot the u-blox driver gives this heading itself (RELPOSNED, clockwise from north):
yaw_enu = 90 deg - heading_ned. Then this node is replaced by a small converter.
"""
import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, NavSatFix

EARTH_RADIUS = 6371000.0  # m, flat-Earth approximation is fine over a 0.5 m baseline


class DualGpsHeading(Node):

    def __init__(self):
        super().__init__('dual_gps_heading')
        # parameters: change with --ros-args -p name:=value
        self.baseline = self.declare_parameter('baseline', 0.5).value              # m, antenna distance
        self.baseline_tolerance = self.declare_parameter('baseline_tolerance', 0.1).value  # m
        self.position_std = self.declare_parameter('position_std', 0.01).value     # m, RTK fix
        self.frame_id = self.declare_parameter('frame_id', 'caretta_base_link').value

        # yaw uncertainty from two noisy antenna positions over the baseline
        self.yaw_std = math.sqrt(2.0) * self.position_std / self.baseline           # rad

        self.front = None   # last front fix
        self.create_subscription(NavSatFix, '/gps/front/fix', self.on_front, 10)
        self.create_subscription(NavSatFix, '/gps/rear/fix', self.on_rear, 10)
        self.pub = self.create_publisher(Imu, '/gps/heading', 10)
        self.get_logger().info(
            f'baseline {self.baseline:.2f} m, position std {self.position_std * 100:.1f} cm '
            f'-> heading std {math.degrees(self.yaw_std):.1f} deg')

    def on_front(self, msg):
        self.front = msg

    def on_rear(self, rear):
        """Compute and publish the heading every time a rear fix arrives."""
        front = self.front
        if front is None:
            return
        # no fix on one antenna (real receiver: also no RTK) -> no heading
        if rear.status.status < 0 or front.status.status < 0:
            return

        # front - rear in metres (east, north)
        lat = math.radians(rear.latitude)
        d_north = math.radians(front.latitude - rear.latitude) * EARTH_RADIUS
        d_east = math.radians(front.longitude - rear.longitude) * EARTH_RADIUS * math.cos(lat)

        # a wrong baseline means a bad fix (lost RTK, multipath): skip it
        measured = math.hypot(d_north, d_east)
        if abs(measured - self.baseline) > self.baseline_tolerance:
            self.get_logger().warn(
                f'baseline {measured:.2f} m, expected {self.baseline:.2f} m: heading skipped',
                throttle_duration_sec=2.0)
            return

        yaw = math.atan2(d_north, d_east)   # ENU: east = 0, north = +90 deg

        msg = Imu()
        msg.header.stamp = rear.header.stamp
        msg.header.frame_id = self.frame_id
        msg.orientation.z = math.sin(yaw / 2.0)
        msg.orientation.w = math.cos(yaw / 2.0)
        # only yaw is measured: roll/pitch unknown, no angular velocity / acceleration
        msg.orientation_covariance[0] = 1e6
        msg.orientation_covariance[4] = 1e6
        msg.orientation_covariance[8] = self.yaw_std ** 2
        msg.angular_velocity_covariance[0] = -1.0
        msg.linear_acceleration_covariance[0] = -1.0

        self.pub.publish(msg)
        self.get_logger().info(f'heading {math.degrees(yaw):+6.1f} deg', throttle_duration_sec=1.0)


def main():
    rclpy.init()
    node = DualGpsHeading()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
