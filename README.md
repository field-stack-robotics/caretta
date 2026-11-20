# Caretta

FS-1 Caretta differential-drive robot by Field Stack Robotics. ROS 2 Humble.

## Build

```bash
cd caretta_ws
colcon build
source install/setup.bash
```

## Run

View the model in RViz:

```bash
ros2 launch caretta_description display.launch.py
```

Run the simulation in Gazebo (needs `caretta_simulator`):

```bash
ros2 launch caretta_gazebo gazebo.launch.py rviz:=true
```

Drive it:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r cmd_vel:=/diff_drive_controller/cmd_vel_unstamped
```

## Topics

- `/scan`: LiDAR
- `/camera/image_raw`: camera
- `/diff_drive_controller/odom`: odometry
