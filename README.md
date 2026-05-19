# YMA Quadruped ROS2
<img width="3168" height="1344" alt="Gemini_Generated_Image_kb07otkb07otkb07(2)" src="https://github.com/user-attachments/assets/939afc75-5fc8-49e8-b7fd-eb651436626a" />
<br>

This repo is for my quadruped robot (code, 3D files, etc.). <br>
This walking robot can autonomously navigate thanks to Nav2 and SLAM. I built this with ROS 2 Jazzy, running on an ESP32 and a Raspberry Pi.<br>
My goal is to show examples of how to make your own autonomous quadruped with ROS 2.<br>
## What it can do
https://github.com/user-attachments/assets/2a4f5992-fd1c-4fa5-9b9c-b5832c5c24f9
## Why making a quadruped
The answer is easy! **To learn new stuff!**
<br>
I faced many challenges but I will guide you through everything. 

# Installation
```
cd ~/ros2_ws/src
git clone https://github.com/joschmaCYU/quadruped/
cd quadruped/docker
bash build.sh
```
# Usage
You can either use the GUI:
```
python3 src/quadruped_basics/dashboard.py
```
Or you can use the terminal
## For sim
```
ros2 launch quadruped sim.amcl.launch.py
```
or 
```
ros2 launch quadruped sim.slam.launch.py
```
## For the real robot
```
ros2 launch quadruped real.amcl.launch.py
```
or
```
ros2 launch quadruped real.slam.launch.py
```

# Tutorial -your turn to build (🚧 work in progress 🚧):
Follow these steps to build your own quadruped !

### 0 - What will my robot do ?
The first question you have to ask your self and the most important one is: *what will my robot do ?*<br>
For me, I want my robot to autonomously navigate a semi-controlled environement.

### 1 - Parts
Now that you have defined your goals you need to pick your parts.<br>
I choose:
- Compute: Raspberry Pi 4 (Main ROS 2 brain) and ESP32 (Servo controller)
- Actuators: 8x MG90S Micro Servos
- Sensors: 2D LiDAR (for SLAM/Navigation) and an IMU
> [!WARNING]
> You should really use an IMU else the odometry will be very difficult to work with

For more details see [parts](https://github.com/joschmaCYU/quadruped/blob/main/PartsREADME.md)

### 2 - Print & Assemble
Now that you know what we have to fit in our robot lets design it. Use your favorite CAD software and create your URDF file.<br>
For more help see [print](https://github.com/joschmaCYU/quadruped/blob/main/PrintREADME.md)

### 3 - Simulating the robot and let's use ROS
Now that you have your urdf file we can simulate it!<br>
The robot runs on ROS 2 Jazzy. It handles the communication between the sensors, actuators, the Pi, and the ESP32. <br> 
[Let's bring your robot to sim](https://github.com/joschmaCYU/quadruped/blob/main/SimREADME.md)<br>

#### Teleoperation
Now that you implemented everything to make the robot let's make it move!<br>
You will have to [launch gz-sim and run the urdf spawn script](https://gazebosim.org/docs/latest/spawn_urdf/)<br>
```ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p use_sim_time:=true```
<br>
<details>
<summary>Click to view the summary of ros2 topics (for sim):</summary>
    
```mermaid
graph TD
    %% Define Styles
    classDef input fill:#27ae60,stroke:#2ecc71,stroke-width:2px,color:#fff
    classDef core fill:#8e44ad,stroke:#9b59b6,stroke-width:2px,color:#fff
    classDef sim fill:#d35400,stroke:#e67e22,stroke-width:2px,color:#fff
    classDef viz fill:#2980b9,stroke:#3498db,stroke-width:2px,color:#fff

    subgraph User_Input ["User Control"]
        TELEOP("teleop_twist_keyboard<br>(or Joystick)"):::input
    end

    subgraph ROS2_Logic ["ROS 2 Brain"]
        IK_NODE("ik_node.py<br>(Quadruped Kinematics)"):::core
        RSP("robot_state_publisher<br>(URDF Parsing)"):::core
    end

    subgraph Simulation ["Gazebo Physics Engine"]
        BRIDGE("ros_gz_bridge<br>(Sensor Translator)"):::sim
        R2C("ros2_control<br>(Virtual Servos)"):::sim
    end

    subgraph Mapping_and_Viz ["Mapping & Visualization"]
        SLAM("SLAM Toolbox"):::viz
        RVIZ("RViz 2"):::viz
    end

    %% --- COMMAND FLOW (How it moves) ---
    TELEOP -->|" /cmd_vel (Twist)"| IK_NODE
    IK_NODE -->|" /joint_group_position_controller/commands"| R2C
    
    %% --- SENSOR FLOW (How it sees/feels) ---
    BRIDGE -->|" /imu (Imu)"| IK_NODE
    BRIDGE -->|" /scan (LaserScan)"| SLAM
    BRIDGE -->|" /scan (LaserScan)"| RVIZ
    
    %% --- ODOMETRY & MAPPING FLOW ---
    IK_NODE -->|" /odom (Odometry)"| SLAM
    IK_NODE -->|" /odom (Odometry)"| RVIZ
    SLAM -->|" /map (OccupancyGrid)"| RVIZ

    %% --- TF TREE (Coordinate Math - Dotted Lines) ---
    SLAM -.->|" /tf (map -> odom)"| RVIZ
    IK_NODE -.->|" /tf (odom -> base_footprint)"| RVIZ
    RSP -.->|" /tf_static (Body Links)"| RVIZ
```

</details>
    
### 4 - Navigation
For this we will need to use gz-sim in combination with either AMCL and SLAM
#### 4.1 - SLAM
This will be used to create the map
#### 4.2 - AMCL

### 5 - Bulding the robot
### 6 - Sim to life
We will be using Micro-ROS to connect our raspberry pi to our esp32. So our esp can send and read topics!<br>
<br>
<details>
<summary>Click to view the summary of our ros2 topics when running the real robot</summary>
    
```mermaid
graph TD
    %% Define Styles
    classDef autonomy fill:#2980b9,stroke:#3498db,stroke-width:2px,color:#fff
    classDef core fill:#8e44ad,stroke:#9b59b6,stroke-width:2px,color:#fff
    classDef drivers fill:#c0392b,stroke:#e74c3c,stroke-width:2px,color:#fff
    classDef mros fill:#27ae60,stroke:#2ecc71,stroke-width:2px,color:#fff
    
    subgraph High_Level_Autonomy ["High-Level Autonomy (Nav2 & SLAM)"]
        NAV2("Nav2 Stack<br>(Planner, Controller, BT Navigator)"):::autonomy
        SLAM("SLAM Toolbox<br>(Map Generation)"):::autonomy
    end

    subgraph Robot_Core_Logic ["Robot Core Logic"]
        IK_NODE("ik_node.py<br>(Quadruped Kinematics)"):::core
        RSP("robot_state_publisher<br>(URDF Parsing)"):::core
        TF_STATIC("static_transform_publisher<br>(base_footprint -> base_laser)"):::core
    end

    subgraph Hardware_Drivers ["Hardware Drivers"]
        LIDAR_NODE("ldlidar_stl_ros2_node"):::drivers
        AGENT("micro_ros_agent<br>(Serial Bridge)"):::mros
    end

    subgraph ESP32_Microcontroller ["ESP32 (Micro-ROS Node)"]
        ESP_NODE("ESP32<br>(IMU & Servo Control)"):::mros
    end

    %% --- TOPIC CONNECTIONS (Data Flow) ---
    
    %% Sensors to Brain
    LIDAR_NODE -->|"/scan (LaserScan)"| SLAM
    LIDAR_NODE -->|"/scan (LaserScan)"| NAV2
    
    %% Movement Commands
    NAV2 -->|"/cmd_vel (Twist)"| IK_NODE
    
    %% Kinematics to Hardware
    IK_NODE -->|"/joint_group_position_controller/commands"| AGENT
    AGENT ====|"UART/Serial Bridge"| ESP_NODE
    
    %% Hardware Feedback to Brain
    ESP_NODE ====|"UART/Serial Bridge"| AGENT
    AGENT -->|"/imu (Imu)"| IK_NODE
    AGENT -->|"/imu (Imu)"| NAV2
    
    %% Odometry Feedback
    IK_NODE -->|"/odom (Odometry)"| NAV2
    IK_NODE -->|"/odom (Odometry)"| SLAM

    %% --- TF TREE CONNECTIONS (Coordinate Math - Dotted Lines) ---
    SLAM -.->|"/tf (map -> odom)"| NAV2
    IK_NODE -.->|"/tf (odom -> base_footprint)"| NAV2
    RSP -.->|"/tf_static (Body Links)"| NAV2
    TF_STATIC -.->|"/tf_static (base_laser)"| NAV2
```

</details>

<details>
<summary>FAQ</summary>
Should I program in Python or C++ ? <br> At the start for quick iteration you can use python and if the performance requires it switch to c++. <br><br>
</details>
