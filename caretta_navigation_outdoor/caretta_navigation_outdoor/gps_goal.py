"""GPS goals from the RViz "GpsGoal" panel (caretta_rviz_plugins) to Nav2.

  in:  /gps_goal         geographic_msgs/GeoPoseStamped  lat/lon (+ heading; NaN = face the way it drives)
       /gps_goal/cancel  std_msgs/Empty                  cancel the running goal
       /clicked_point    geometry_msgs/PointStamped      RViz "Publish Point" click (map frame)
  out: /gps_goal/status  std_msgs/String                 shown in the panel
       /gps_goal/clicked geographic_msgs/GeoPoint        the click in lat/lon (fills the panel)
Converts with navsat_transform (/fromLL, /toLL) and sends NavigateToPose to Nav2.
"""
import math

from action_msgs.msg import GoalStatus
from geographic_msgs.msg import GeoPoint, GeoPoseStamped
from geometry_msgs.msg import PointStamped, PoseStamped
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import Odometry
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from robot_localization.srv import FromLL, ToLL
from std_msgs.msg import Empty, String


class GpsGoal(Node):

    def __init__(self):
        super().__init__('gps_goal')
        # the global costmap is a rolling window around the robot: goals must be inside it
        self.max_distance = self.declare_parameter('max_distance', 38.0).value   # m

        self.from_ll = self.create_client(FromLL, 'fromLL')
        self.to_ll = self.create_client(ToLL, 'toLL')
        self.nav = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.status_pub = self.create_publisher(String, '/gps_goal/status', 10)
        self.clicked_pub = self.create_publisher(GeoPoint, '/gps_goal/clicked', 10)
        self.create_subscription(GeoPoseStamped, '/gps_goal', self.on_goal, 10)
        self.create_subscription(Empty, '/gps_goal/cancel', self.on_cancel, 10)
        self.create_subscription(PointStamped, '/clicked_point', self.on_click, 10)
        self.create_subscription(Odometry, '/odometry/global', self.on_odom, 10)
        self.robot = None          # (x, y) in map
        self.goal_handle = None
        self.last_feedback = 0.0

    def status(self, text):
        self.get_logger().info(text)
        self.status_pub.publish(String(data=text))

    def on_odom(self, msg):
        self.robot = (msg.pose.pose.position.x, msg.pose.pose.position.y)

    # ---- RViz click -> lat/lon (to fill the panel)
    def on_click(self, msg):
        if not self.to_ll.service_is_ready():
            self.status('navsat_transform (/toLL) is not running.')
            return
        req = ToLL.Request()
        req.map_point = msg.point
        self.to_ll.call_async(req).add_done_callback(self.on_click_ll)

    def on_click_ll(self, future):
        ll = future.result().ll_point
        if ll.latitude == 0.0 and ll.longitude == 0.0:
            self.status('navsat_transform has no GPS transform yet: wait a few seconds.')
            return
        self.clicked_pub.publish(GeoPoint(latitude=ll.latitude, longitude=ll.longitude, altitude=0.0))
        self.status(f'clicked: lat {ll.latitude:.7f}, lon {ll.longitude:.7f}')

    # ---- panel goal -> map -> Nav2
    def on_goal(self, msg):
        if not self.from_ll.service_is_ready():
            self.status('navsat_transform (/fromLL) is not running: start gps_navigation.launch.py.')
            return
        req = FromLL.Request()
        req.ll_point = GeoPoint(latitude=msg.pose.position.latitude,
                                longitude=msg.pose.position.longitude, altitude=0.0)
        q = msg.pose.orientation
        yaw = None if math.isnan(q.w) else math.atan2(2.0 * q.w * q.z, 1.0 - 2.0 * q.z * q.z)
        self.from_ll.call_async(req).add_done_callback(lambda f: self.send_goal(f, yaw))

    def send_goal(self, future, yaw):
        p = future.result().map_point
        if self.robot is not None:
            dist = math.dist(self.robot, (p.x, p.y))
            if dist > self.max_distance:
                self.status(f'goal is {dist:.0f} m away (max {self.max_distance:.0f} m, '
                            'outside the costmap): pick a closer point.')
                return
            if yaw is None:   # face the way it drives
                yaw = math.atan2(p.y - self.robot[1], p.x - self.robot[0])
        if yaw is None:
            yaw = 0.0
        if not self.nav.wait_for_server(timeout_sec=1.0):
            self.status('Nav2 (navigate_to_pose) is not running.')
            return

        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x = p.x
        goal.pose.pose.position.y = p.y
        goal.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal.pose.pose.orientation.w = math.cos(yaw / 2.0)
        self.status(f'goal at map ({p.x:+.1f}, {p.y:+.1f}) m, heading {math.degrees(yaw):.0f} deg')
        send = self.nav.send_goal_async(goal, feedback_callback=self.on_feedback)
        send.add_done_callback(self.on_accepted)

    def on_accepted(self, future):
        handle = future.result()
        if not handle.accepted:
            self.status('Nav2 rejected the goal.')
            return
        self.goal_handle = handle
        handle.get_result_async().add_done_callback(self.on_result)

    def on_feedback(self, msg):
        now = self.get_clock().now().nanoseconds * 1e-9
        if now - self.last_feedback > 1.0:     # at most once a second
            self.last_feedback = now
            self.status(f'driving: {msg.feedback.distance_remaining:.1f} m left')

    def on_result(self, future):
        code = future.result().status
        self.goal_handle = None
        text = {GoalStatus.STATUS_SUCCEEDED: 'goal reached',
                GoalStatus.STATUS_CANCELED: 'goal canceled',
                GoalStatus.STATUS_ABORTED: 'goal failed (no path or stuck)'}.get(code, f'goal ended ({code})')
        self.status(text)

    def on_cancel(self, _msg):
        if self.goal_handle is None:
            self.status('no goal running')
            return
        self.goal_handle.cancel_goal_async()
        self.status('canceling ...')


def main():
    rclpy.init()
    node = GpsGoal()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
