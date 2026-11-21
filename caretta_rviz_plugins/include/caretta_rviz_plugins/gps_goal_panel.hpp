// GPS goal panel for RViz: type latitude / longitude (+ optional heading), press Go.
// The panel only talks on topics; the gps_goal node (caretta_navigation_outdoor) converts the
// point with /fromLL and sends it to Nav2.
//   out: /gps_goal         geographic_msgs/GeoPoseStamped (heading NaN = face the way it drives)
//        /gps_goal/cancel  std_msgs/Empty
//   in:  /gps_goal/status  std_msgs/String  (shown under the buttons)
//        /gps_goal/clicked geographic_msgs/GeoPoint (RViz "Publish Point" click, fills the fields)
#ifndef CARETTA_RVIZ_PLUGINS__GPS_GOAL_PANEL_HPP_
#define CARETTA_RVIZ_PLUGINS__GPS_GOAL_PANEL_HPP_

#include <QLabel>
#include <QLineEdit>

#include <geographic_msgs/msg/geo_point.hpp>
#include <geographic_msgs/msg/geo_pose_stamped.hpp>
#include <rclcpp/rclcpp.hpp>
#include <rviz_common/panel.hpp>
#include <std_msgs/msg/empty.hpp>
#include <std_msgs/msg/string.hpp>

namespace caretta_rviz_plugins
{

class GpsGoalPanel : public rviz_common::Panel
{
  Q_OBJECT

public:
  explicit GpsGoalPanel(QWidget * parent = nullptr);
  void onInitialize() override;
  void load(const rviz_common::Config & config) override;
  void save(rviz_common::Config config) const override;

private Q_SLOTS:
  void onGo();
  void onCancel();

private:
  void setStatus(const QString & text);

  QLineEdit * lat_edit_;
  QLineEdit * lon_edit_;
  QLineEdit * heading_edit_;
  QLabel * status_label_;

  rclcpp::Node::SharedPtr node_;
  rclcpp::Publisher<geographic_msgs::msg::GeoPoseStamped>::SharedPtr goal_pub_;
  rclcpp::Publisher<std_msgs::msg::Empty>::SharedPtr cancel_pub_;
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr status_sub_;
  rclcpp::Subscription<geographic_msgs::msg::GeoPoint>::SharedPtr clicked_sub_;
};

}  // namespace caretta_rviz_plugins

#endif  // CARETTA_RVIZ_PLUGINS__GPS_GOAL_PANEL_HPP_
