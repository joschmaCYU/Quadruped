### 3 - Simulating the robot
#### 3.1 - What is ROS and what will we be using ROS for ?
The most simple explanation I can give is : ROS is like whatsapp a messaging app but the messages are information. We will be using ROS to benefit from it's great echo system (simulators, autonomus navigation, mapping...).
> [!TIP]
> If you have never used ROS you should begging with getting familiar to it with [tutorials](https://docs.ros.org/en/jazzy/Tutorials.html) !

<details>
<summary>This is how it will work:</summary>

```mermaid
graph TD
    %% Define Styles
    classDef pc fill:#2c3e50,stroke:#34495e,stroke-width:2px,color:#ecf0f1
    classDef esp fill:#27ae60,stroke:#2ecc71,stroke-width:2px,color:#fff
    classDef sensor fill:#c0392b,stroke:#e74c3c,stroke-width:2px,color:#fff
    classDef actuator fill:#e67e22,stroke:#d35400,stroke-width:2px,color:#fff
    classDef software fill:#2980b9,stroke:#3498db,stroke-width:2px,color:#fff
    subgraph Main_Computer ["Main Computer (PC or Raspberry Pi)"]
        ROS2("ROS 2 Environment<br>(Nav2, SLAM, IK Node)"):::software
        U_Agent("Micro-ROS Agent<br>(Docker)"):::software
        L_Node("LD19 LiDAR Node"):::software

        ROS2 <-->|"ROS 2 Topics<br>(/cmd_vel, /odom)"| U_Agent
        L_Node -->|"ROS 2 Topic<br>(/scan)"| ROS2
    end

    subgraph Microcontroller ["Microcontroller"]
        ESP32("ESP32<br>(Micro-ROS Client)"):::esp
    end

    subgraph Peripherals ["Sensors & Actuators"]
        LD19("LD19 LiDAR"):::sensor
        IMU("BNO085 IMU"):::sensor
        Servos("8x Quadruped Servos<br>(Legs)"):::actuator
    end

    %% Hardware Connections
    U_Agent <-->|"USB Cable<br>(/dev/ttyUSB0)"| ESP32
    L_Node <-->|"USB Cable<br>(/dev/ttyUSB1)"| LD19

    ESP32 <-->|"I2C (SDA, SCL, 3.3V, GND)"| IMU
    ESP32 -->|"PWM / Servo Control Board"| Servos

    %% Apply Styles
    class Main_Computer pc
    class Microcontroller esp
    class Peripherals pc
```

</details>

[!TIP]
> We will use gz-sim for simulation but there are other alternatives.

#### 3.2 - Set up urdf + sim
You can find a tutorial to do so [here](https://github.com/MOGI-ROS/Week-3-4-Gazebo-basics). I will not detail this part which is outside of this tutorial scope.

#### 3.2 - Making the robot move
To make the robot move we will use inverse kinematics.<br>
If you don't want to build this I am sure you can find some pre-built frameworks like ros2_control walking plugins to do the job for you but here we will create our own !
<br>
Because we use reptilian design we need to keep in minde that:
1) The upper leg (L1) is permanently sticking straight out horizontally.
2) The knee joint tilts the lower leg (L2) outward to control the robot's height.
3) The shoulder joint acts as a "yaw" hinge, sweeping the entire leg forward and backward like a door to control the stride.

Here is a small animation to visualise the math
<img width="800" height="600" alt="spider_leg_ik" src="https://github.com/user-attachments/assets/1aada248-f842-4fe2-8e4b-0bc4cc5b8886" />
This code is used to calculate how to reach the give x and y coordinates
```
def calculate_ik(self, x, z):
        # 1. Physical Leg Lengths
        L1 = 0.206  # length of upper leg
        L2 = 0.250  # length of lower leg

        cos_knee = abs(z) / L2
        knee_angle = math.acos(cos_knee)

        horizontal_reach = L1 + (L2 * math.sin(knee_angle))
        step_reach = x / horizontal_reach
        shoulder_angle = math.asin(step_reach)

        return shoulder_angle, knee_angle
```
The math isn't very advanced but you need to take your time to assimilate it!<br>

#### 3.3 - IK gait
The gait is used to tell each foot exactly where it needs to be in 3D space
```
 def get_ik_gait(self, t, phase_offset, step_scale):
        # One full step cycle takes 0.8 seconds.
        T = 0.80
        # The leg spends 60% on the ground pushing the robot forward
        duty_factor = 0.60
        cycle_progress = ((t / T) + phase_offset) % 1.0

        stride_length = 0.25  # 15cm max steps
        step_height = 0.08    # Lift foot 8cm into the air
        stand_height = -0.25  # Keep the hip 20cm off the floor (Safe for L2=25cm)

        if cycle_progress < duty_factor:
            # STANCE PHASE
            stance_p = cycle_progress / duty_factor
            target_x = (stride_length / 2.0) - (stride_length * stance_p)
            target_z = stand_height
        else:
            # SWING PHASE
            swing_p = (cycle_progress - duty_factor) / (1.0 - duty_factor)
            target_x = -(stride_length / 2.0) + (stride_length * swing_p)
            target_z = stand_height + (step_height * math.sin(swing_p * math.pi))

        # SCALE THE PHYSICAL STEP (Not the joint angle!)
        target_x = target_x * step_scale

        return self.calculate_ik(target_x, target_z)

```

#### 3.4 - Odom & Kinematics
The odom code has two main jobs: guessing where the robot is (Odometry) and moving the legs (Kinematics).<br>

Guessing:
```
# How much the robot should move forward in sim
speed_multiplier = xx

# Guess new position based on speed and the IMU's compass direction
self.odom_x += (self.cmd_x * self.speed_multiplier * math.cos(self.odom_yaw)) * self.dt
self.odom_y += (self.cmd_x * self.speed_multiplier * math.sin(self.odom_yaw)) * self.dt
```

Turning:
```
    # Turn by making one side take larger steps
    amp_FL = self.cmd_x - (self.cmd_w * 1.5)
    amp_FR = self.cmd_x + (self.cmd_w * 1.5)
    amp_BL = self.cmd_x - (self.cmd_w * 1.5)
    amp_BR = self.cmd_x + (self.cmd_w * 1.5)

    # Diagonal pairs move together (Phase 0.0 vs 0.5)
    shoulder_FL, knee_FL = self.get_ik_gait(self.walk_time, 0.0, amp_FL)
    shoulder_BR, knee_BR = self.get_ik_gait(self.walk_time, 0.0, amp_BR)

    shoulder_FR, knee_FR = self.get_ik_gait(self.walk_time, 0.5, amp_FR)
    shoulder_BL, knee_BL = self.get_ik_gait(self.walk_time, 0.5, amp_BL)
```

You will need to tweak your speed multiplier to fit to the speed of your robot.<br>
You just have to publish it to /odom<br>
<br>
One of the many chalenges of making a walking robot is friction and foot slippage. Even in simulation, the robot rarely moves exactly as commanded, causing odometry to not represent the real robot position. To compensate it we will use our IMU in combination of our speed_multiplier

Now we will try to make the robot [move](https://github.com/joschmaCYU/quadruped#teleoperation)
