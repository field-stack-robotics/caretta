"""Show the top-down image of the Gazebo outdoor world under the robot in RViz.

Publishes a Marker (textured plane, media/outdoor_ground.dae + .jpg) in the map frame, sized and
placed so that the image lines up with the Gazebo world (map = Gazebo world: x east, y north).
The image was rendered once from a camera 240 m above caretta_outdoor.sdf; it covers
x -10..40 m, y -10..30 m. Re-render it if the world changes.
  out: /outdoor_ground (visualization_msgs/Marker, every 2 s)
"""
import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker


class OutdoorGround(Node):

    def __init__(self):
        super().__init__('outdoor_ground')
        mesh = self.declare_parameter(
            'mesh', 'package://caretta_navigation_outdoor/media/outdoor_ground.dae').value
        m = Marker()
        m.header.frame_id = self.declare_parameter('frame_id', 'map').value
        m.ns = 'outdoor_ground'
        m.id = 0
        m.type = Marker.MESH_RESOURCE
        m.action = Marker.ADD
        m.mesh_resource = mesh
        m.mesh_use_embedded_materials = True   # with colour (0, 0, 0, 0): use the texture as is
        m.pose.position.x = self.declare_parameter('center_x', 15.0).value
        m.pose.position.y = self.declare_parameter('center_y', 10.0).value
        m.pose.position.z = -0.01               # just below the grid and the costmaps
        m.pose.orientation.w = 1.0
        m.scale.x = self.declare_parameter('size_x', 50.0).value
        m.scale.y = self.declare_parameter('size_y', 40.0).value
        m.scale.z = 1.0
        self.marker = m
        self.pub = self.create_publisher(Marker, '/outdoor_ground', 1)
        self.create_timer(2.0, self.publish)

    def publish(self):
        self.marker.header.stamp = self.get_clock().now().to_msg()
        self.pub.publish(self.marker)


def main():
    rclpy.init()
    node = OutdoorGround()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
