# Sim to Life (The Micro-ROS Bridge)

The magic of ROS 2 is that the "brain" (your Python kinematics and Nav2 planners) does not care if the robot is a Gazebo simulation or physical plastic. It just publishes to topics and waits for a response.

## The Architecture
To bridge the physical hardware to the ROS 2 network, we use a distributed system:

1.  **The ESP32 (The Muscles):** Flashed with a Micro-ROS node (via Arduino IDE). It subscribes to `/joint_group_position_controller/commands` to move the physical servos and publishes `/gyro_z_speed` at 50Hz directly from the I2C bus.
2.  **The Raspberry Pi (The Brain):** Handles the heavy logic: Nav2, Python Inverse Kinematics, and LiDAR drivers. It runs a Dockerized, architecture-aware ROS 2 Jazzy environment.
3.  **The Bridge:** The Pi runs `micro_ros_agent`. It actively listens to the USB serial port (`/dev/ttyUSB0`) connected to the ESP32 and seamlessly translates the microcontroller's raw serial data into standard ROS 2 topics.

---

## Roadblocks & Solutions: Bridging Software to Reality

Translating perfect simulation math to messy physical hardware required several strict code adjustments.

### Upside-Down LiDAR Logic
**The Problem:** The robot would turn left, but the LiDAR perceived the walls shifting the wrong way, immediately breaking the SLAM map.
**The Fix:** Because the LD19 LiDAR is physically mounted upside down on the 3D-printed chassis, its physical rotation is mechanically reversed. I fixed this in the `real.slam.launch.py` by applying a **3.14159 rad** (180-degree) roll to the `static_transform_publisher` between `base_link` and `base_laser`. This tells ROS 2 the sensor is looking at the floor, natively correcting the Left/Right inversion.

### Moonwalking / Walking in Place
**The Problem:** When sending slow velocity commands (e.g., reversing slowly via teleop), the robot would march aggressively in place without actually moving.
**The Fix:** The Inverse Kinematics (IK) step height was initially hardcoded to lift the foot 8 cm into the air every step, regardless of how small the forward stride was. I updated the IK engine to use a dynamic step height:
`actual_step_height = step_height * min(1.0, max(0.2, abs(step_scale)))`
Now, tiny movement requests result in smooth, low-profile shuffles rather than aggressive stomps.

### CycloneDDS Type Hash Mismatch
**The Problem:** The Raspberry Pi continuously threw `[WARN] Failed to parse type hash for topic` for the IMU, and `ros2 topic echo /imu` returned absolutely nothing.
**The Fix:** ROS 2 Jazzy utilizes updated Interface Definition Language (IDL) hashes (RIHS) that didn't perfectly match the older Micro-ROS Arduino library's complex `sensor_msgs/Imu` struct. Because the robot only strictly needed the Z-axis angular velocity to correct its odometry, I bypassed the complex struct entirely. I rewrote the ESP32 code to publish a simple `std_msgs/Float64` containing only the gyroscope's Z-axis float, which passed through the CycloneDDS bridge flawlessly.
