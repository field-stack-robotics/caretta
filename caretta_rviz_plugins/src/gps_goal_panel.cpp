#include "caretta_rviz_plugins/gps_goal_panel.hpp"

#include <QGridLayout>
#include <QHBoxLayout>
#include <QPushButton>
#include <QVBoxLayout>

#include <cmath>
#include <limits>

#include <pluginlib/class_list_macros.hpp>
#include <rviz_common/display_context.hpp>

namespace caretta_rviz_plugins
{

GpsGoalPanel::GpsGoalPanel(QWidget * parent)
: rviz_common::Panel(parent)
{
  lat_edit_ = new QLineEdit();
  lon_edit_ = new QLineEdit();
  heading_edit_ = new QLineEdit();
  lat_edit_->setPlaceholderText("e.g. 52.000090");
  lon_edit_->setPlaceholderText("e.g. 5.000146");
  heading_edit_->setPlaceholderText("empty = face the way it drives");
  heading_edit_->setToolTip("degrees, 0 = east, 90 = north (ROS / ENU)");

  auto * grid = new QGridLayout();
  grid->addWidget(new QLabel("Latitude"), 0, 0);
  grid->addWidget(lat_edit_, 0, 1);
  grid->addWidget(new QLabel("Longitude"), 1, 0);
  grid->addWidget(lon_edit_, 1, 1);
  grid->addWidget(new QLabel("Heading [deg]"), 2, 0);
  grid->addWidget(heading_edit_, 2, 1);

  auto * go_button = new QPushButton("Go");
  auto * cancel_button = new QPushButton("Cancel");
  auto * buttons = new QHBoxLayout();
  buttons->addWidget(go_button);
  buttons->addWidget(cancel_button);

  status_label_ = new QLabel("Tip: \"Publish Point\" tool + click on the map fills lat/lon.");
  status_label_->setWordWrap(true);

  auto * layout = new QVBoxLayout();
  layout->addLayout(grid);
  layout->addLayout(buttons);
  layout->addWidget(status_label_);
  setLayout(layout);

  connect(go_button, &QPushButton::clicked, this, &GpsGoalPanel::onGo);
  connect(cancel_button, &QPushButton::clicked, this, &GpsGoalPanel::onCancel);
  connect(lon_edit_, &QLineEdit::returnPressed, this, &GpsGoalPanel::onGo);
}

void GpsGoalPanel::onInitialize()
{
  node_ = getDisplayContext()->getRosNodeAbstraction().lock()->get_raw_node();
  goal_pub_ = node_->create_publisher<geographic_msgs::msg::GeoPoseStamped>("/gps_goal", 10);
  cancel_pub_ = node_->create_publisher<std_msgs::msg::Empty>("/gps_goal/cancel", 10);

  // callbacks come from the ROS executor: hand the text over to the Qt (GUI) thread
  status_sub_ = node_->create_subscription<std_msgs::msg::String>(
    "/gps_goal/status", 10, [this](const std_msgs::msg::String & msg) {
      QString text = QString::fromStdString(msg.data);
      QMetaObject::invokeMethod(this, [this, text]() {setStatus(text);}, Qt::QueuedConnection);
    });
  clicked_sub_ = node_->create_subscription<geographic_msgs::msg::GeoPoint>(
    "/gps_goal/clicked", 10, [this](const geographic_msgs::msg::GeoPoint & p) {
      double lat = p.latitude, lon = p.longitude;
      QMetaObject::invokeMethod(
        this, [this, lat, lon]() {
          lat_edit_->setText(QString::number(lat, 'f', 7));
          lon_edit_->setText(QString::number(lon, 'f', 7));
          setStatus("Clicked point filled in. Press Go.");
        }, Qt::QueuedConnection);
    });
}

void GpsGoalPanel::onGo()
{
  bool lat_ok = false, lon_ok = false;
  double lat = lat_edit_->text().trimmed().toDouble(&lat_ok);
  double lon = lon_edit_->text().trimmed().toDouble(&lon_ok);
  if (!lat_ok || !lon_ok || std::abs(lat) > 90.0 || std::abs(lon) > 180.0) {
    setStatus("Latitude/longitude are not valid numbers.");
    return;
  }

  // heading: empty -> NaN (the gps_goal node faces the robot the way it drives)
  double yaw = std::numeric_limits<double>::quiet_NaN();
  QString heading_text = heading_edit_->text().trimmed();
  if (!heading_text.isEmpty()) {
    bool ok = false;
    double deg = heading_text.toDouble(&ok);
    if (!ok) {
      setStatus("Heading is not a number (leave it empty to skip).");
      return;
    }
    yaw = deg * M_PI / 180.0;
  }

  geographic_msgs::msg::GeoPoseStamped goal;
  goal.header.stamp = node_->now();
  goal.header.frame_id = "wgs84";
  goal.pose.position.latitude = lat;
  goal.pose.position.longitude = lon;
  goal.pose.position.altitude = 0.0;
  if (std::isnan(yaw)) {
    goal.pose.orientation.w = std::numeric_limits<double>::quiet_NaN();
  } else {
    goal.pose.orientation.z = std::sin(yaw / 2.0);
    goal.pose.orientation.w = std::cos(yaw / 2.0);
  }
  goal_pub_->publish(goal);
  setStatus(QString("Sent lat %1, lon %2 ...").arg(lat, 0, 'f', 7).arg(lon, 0, 'f', 7));
}

void GpsGoalPanel::onCancel()
{
  cancel_pub_->publish(std_msgs::msg::Empty());
  setStatus("Cancel sent.");
}

void GpsGoalPanel::setStatus(const QString & text)
{
  status_label_->setText(text);
}

// remember the last typed point in the RViz config
void GpsGoalPanel::save(rviz_common::Config config) const
{
  rviz_common::Panel::save(config);
  config.mapSetValue("Latitude", lat_edit_->text());
  config.mapSetValue("Longitude", lon_edit_->text());
  config.mapSetValue("Heading", heading_edit_->text());
}

void GpsGoalPanel::load(const rviz_common::Config & config)
{
  rviz_common::Panel::load(config);
  QString text;
  if (config.mapGetString("Latitude", &text)) {lat_edit_->setText(text);}
  if (config.mapGetString("Longitude", &text)) {lon_edit_->setText(text);}
  if (config.mapGetString("Heading", &text)) {heading_edit_->setText(text);}
}

}  // namespace caretta_rviz_plugins

PLUGINLIB_EXPORT_CLASS(caretta_rviz_plugins::GpsGoalPanel, rviz_common::Panel)
