# Caretta

FS-1 Caretta differential-drive robot by Field Stack Robotics.

Tested on Ubuntu 22.04, ROS 2 Humble, Ignition Gazebo Fortress.

## Setup

Install [ROS 2 Humble](https://docs.ros.org/en/humble/Installation.html) first.

### 1. Install the tools

Install rosdep (installs package dependencies), colcon (builds the workspace) and git (downloads the repos):

```bash
sudo apt install python3-rosdep python3-colcon-common-extensions git
```

Install the keyboard teleop, used to drive the robot:

```bash
sudo apt install ros-humble-teleop-twist-keyboard
```

### 2. Create the workspace

Create the workspace folder. All packages go inside `src/`:

```bash
mkdir -p ~/caretta_ws/src
```

Go into `src/`:

```bash
cd ~/caretta_ws/src
```

### 3. Clone the repos

Download the robot (model and control):

```bash
git clone -b humble https://github.com/field-stack-robotics/caretta.git
```

Download the Gazebo simulation (skip it if you don't use Gazebo):

```bash
git clone -b humble https://github.com/field-stack-robotics/caretta_simulator.git
```

### 4. Install the dependencies

Go back to the workspace root:

```bash
cd ~/caretta_ws
```

Set up rosdep. This is needed only once per computer; skip it if it says "already exists":

```bash
sudo rosdep init
```

Download the latest list of ROS packages:

```bash
rosdep update
```

Install every package the repos need (Gazebo, ros2_control, ...):

```bash
rosdep install --from-paths src --ignore-src -y
```

### 5. Build

Build all packages in `src/`. This creates the `build/`, `install/` and `log/` folders:

```bash
colcon build
```

Load the built packages into this terminal so `ros2` can find them:

```bash
source install/setup.bash
```

Run `source ~/caretta_ws/install/setup.bash` in every new terminal.

## Workspace layout

```
caretta_ws/
└── src/
    ├── caretta/              # the robot
    │   ├── caretta_description/   # model: URDF, meshes, sensors
    │   ├── caretta_control/       # controllers, twist_mux
    │   ├── caretta_localization/  # EKF (robot_localization)
    │   ├── caretta_navigation/    # indoor: SLAM (slam_toolbox), maps, AMCL, Nav2
    │   ├── caretta_navigation_outdoor/  # outdoor: dual-antenna RTK GPS, GPS localization, Nav2
    │   └── caretta_rviz_plugins/  # RViz GpsGoal panel (latitude/longitude goal)
    └── caretta_simulator/    # Gazebo world and launch
        └── caretta_gazebo/
```

## Run

View the model in RViz:

```bash
ros2 launch caretta_description display.launch.py
```

Run the simulation in Gazebo:

```bash
ros2 launch caretta_gazebo gazebo.launch.py rviz:=true
```

The default world is `caretta_house` (corridor, three rooms, furniture; for SLAM). For the outdoor field (GPS tests) add `world:=caretta_outdoor`, for the small test room `world:=caretta_test`.

Drive it (in a second terminal):

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r cmd_vel:=cmd_vel_teleop
```

Emergency stop (stops every velocity command), and release it:

```bash
ros2 topic pub --once /e_stop std_msgs/msg/Bool "data: true"
ros2 topic pub --once /e_stop std_msgs/msg/Bool "data: false"
```

### Build a map (SLAM)

Start Gazebo without RViz (SLAM opens its own RViz with the map):

```bash
ros2 launch caretta_gazebo gazebo.launch.py
```

Start SLAM (slam_toolbox), in a second terminal:

```bash
ros2 launch caretta_navigation slam.launch.py use_sim_time:=true
```

Drive slowly through every room (teleop above, third terminal), then save the map while SLAM still runs:

```bash
ros2 run nav2_map_server map_saver_cli -f src/caretta/caretta_navigation/maps/caretta_house \
  --ros-args -p use_sim_time:=true
```

### Localize on the saved map (AMCL)

Do not run it together with SLAM: both publish the TF `map` -> `odom`.

```bash
ros2 launch caretta_gazebo gazebo.launch.py
ros2 launch caretta_navigation amcl.launch.py use_sim_time:=true
```

The robot starts at the map origin, so AMCL knows where it is. If it gets lost, set the pose in RViz with
**2D Pose Estimate**, or spread the particles over the whole map and drive a bit:

```bash
ros2 service call /reinitialize_global_localization std_srvs/srv/Empty
```

### Navigate on its own (Nav2)

Starts AMCL, Nav2 and RViz together (do not start `amcl.launch.py` or SLAM as well):

```bash
ros2 launch caretta_gazebo gazebo.launch.py
ros2 launch caretta_navigation navigation.launch.py use_sim_time:=true
```

Give a goal in RViz with **2D Goal Pose**. The keyboard teleop always wins over Nav2, and `/e_stop` stops both.

### Outdoors with GPS (dual-antenna RTK, Nav2 without a map)

Start the outdoor field with the GPS antennas on the robot:

```bash
ros2 launch caretta_gazebo gazebo.launch.py world:=caretta_outdoor gps:=true
```

Start GPS localization, Nav2 and RViz, in a second terminal:

```bash
ros2 launch caretta_navigation_outdoor gps_navigation.launch.py use_sim_time:=true
```

In RViz the ground is a top-down image of the Gazebo world, so the robot drives over the same grass, path and
trees as in Gazebo. Real satellite tiles (`rviz_satellite`, Esri World Imagery, needs internet) are in the
**Satellite** display, off by default; they show the real place at the map origin, not the Gazebo world.

Give a GPS goal in the RViz **GpsGoal** panel: type the latitude and longitude (heading optional) and press **Go**.
With the **Publish Point** tool, a click on the ground fills in the latitude/longitude of that spot.
Two test targets are drawn on the gravel path: **T1** (yellow, 10.6 m) and **T2** (red, 5 m) east of the start, an X
with its latitude/longitude below it; type those into the panel.

Or give a goal in RViz with **2D Goal Pose** (the map frame is the Gazebo world: x east, y north), or drive one lap
of the gravel path with GPS waypoints (latitude, longitude), in a third terminal:

```bash
ros2 run caretta_navigation_outdoor gps_waypoints --ros-args -p use_sim_time:=true
```

## Topics

Sensors:

- `/scan`: LiDAR
- `/camera/image_raw`: camera
- `/imu`: IMU (BNO055, 100 Hz)
- `/diff_drive_controller/odom`: wheel odometry
- `/map`: occupancy grid, from SLAM or from the saved map (TF `map` -> `odom` from SLAM or AMCL)
- `/amcl_pose`, `/particle_cloud`: AMCL estimate and particles
- `/gps/front/fix`, `/gps/rear/fix`: the two GPS antennas (outdoor, `gps:=true`)
- `/gps/heading`: heading from the two antennas; `/odometry/global`: robot in the map from GPS
- `/odometry/filtered`: EKF output, wheel odometry + IMU (also the TF `odom` -> `caretta_base_footprint`)

Velocity commands (`twist_mux` picks one; the higher priority wins):

- `/cmd_vel_teleop`: keyboard, priority 100
- `/cmd_vel`: autonomous navigation (Nav2), priority 10
- `/e_stop`: `std_msgs/Bool`, `true` stops the robot

## License

Apache-2.0
