## Sim to life 
The magic of ROS 2 is that the "brain" (your Python kinematics and Nav2 planners) does not care if the robot is a Gazebo simulation or physical plastic. It just publishes to topics and waits for a response.

### The architecture
To bridge the physical hardware to the ROS 2 network, we use a distributed system:
1.  **The ESP32** Flashed with a micro-ros node (via Arduino IDE). It subscribes to `/joint_group_position_controller/commands` to move the physical servos and publishes `/imu`. 
2.  **The raspberry pi** Handles the heavy logic: Nav2, Python Inverse Kinematics, and LiDAR drivers. It runs a Dockerized, ROS 2 Jazzy environment.
3.  **The bridge:** The Pi runs `micro_ros_agent`. It actively listens to the USB serial port (`/dev/ttyUSB0`) connected to the ESP32 and translates the microcontroller's data into standard ROS 2 topics.

<img width="644" height="466" src="https://www.rototron.info/wp-content/uploads/ESP32_Repair01.jpg" />

### Importing your docker file to your raspberry
#### The architecture problem
Now you need to export your Dockerfile to your raspberry but your CPU architecture is x86_64 but the raspberry is ARM64. So you can't just copy past your Dockerfile. So you will need to compile your Dockerfile from the raspberry pi.

#### The size of the dockerfile
Another problem is that I used a slow sd card with only 16Go. You will need at least 32Go to compile or better if you have a ssd. Then you can export to use on your little 16Go sd card. And to fit on a small size sd card I had to remove the full ros-jazzy-desktop install.

---

### Roadblocks & Solutions: bridging software to reality
Translating perfect simulation math to messy physical hardware required several strict code adjustments.

#### Upside-down LiDAR logic
**The problem:** the robot would turn left, but the LiDAR perceived the walls shifting the wrong way, immediately breaking the SLAM map.
**The fix:** because the LiDAR is physically mounted upside down on the 3D-printed chassis, its physical rotation is mechanically reversed. I fixed this in the `real.slam.launch.py` by applying a **3.14159 rad** (180-degree) roll to the `static_transform_publisher` between `base_link` and `base_laser`. 

#### Moonwalking / walking in place
**The problem:** when sending slow velocity commands (e.g., reversing slowly via teleop), the robot would march aggressively in place without actually moving.
**The fix:** The Inverse Kinematics (IK) step height was initially hardcoded to lift the foot 8 cm into the air every step, regardless of how small the forward stride was. I updated the IK engine to use a dynamic step height:
`actual_step_height = step_height * min(1.0, max(0.2, abs(step_scale)))`
Now, tiny movement requests result in smooth, low-profile shuffles rather than aggressive stomps.
