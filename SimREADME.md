### 3 - Simulating the robot
#### 3.1 - What is ROS and what will we be using ROS for ?
The most simple explanation I can give is : ROS is like whatsapp a messaging app but the messages are information. We will be using ROS to benefit from it's great echo system (simulators, autonomus navigation, mapping...).
> [!TIP]
> If you have never used ROS you should begging with getting familiar to it with [tutorials](https://docs.ros.org/en/jazzy/Tutorials.html) !
#### 3.2 - Set up urdf + sim
You can find a tutorial to do so [here](https://github.com/MOGI-ROS/Week-3-4-Gazebo-basics). I will not detail this part which is outside of this tutorial scope.

#### 3.2 - Making the robot move
To make the robot move we will use inverse kinematics and then use 3d IK to move over obstacles.<br>
If you don't want to build this I am sure you can find some pre-built frameworks like ros2_control walking plugins to do the job for you but here we will create our own !
<br>
1) The upper leg (L1) is permanently sticking straight out horizontally.
2) The knee joint tilts the lower leg (L2) outward to control the robot's height.
3) The shoulder joint acts as a "Yaw" hinge, sweeping the entire leg forward and backward like a door to control the stride.
(sketch how the robot will move to explain the math)

```
def calculate_ik(self, x, z):
        # 1. Physical Leg Lengths
        L1 = 0.206  # length of upper leg
        L2 = 0.250  # length of lower leg

        # 3. KNEE MATH (Controls Height)
        # Because your URDF draws the calf pointing straight down when angle is 0. A larger angle bends it outwards.
        cos_knee = abs(z) / L2
        cos_knee = max(0.0, min(1.0, cos_knee))
        knee_angle = math.acos(cos_knee)

        # 4. SHOULDER MATH (Controls Forward Stride)
        # Calculate how far out the foot currently is due to the knee bend
        horizontal_reach = L1 + (L2 * math.sin(knee_angle))

        # Calculate the sweep angle required to move 'x' meters forward
        step_reach = x / horizontal_reach
        step_reach = max(-1.0, min(1.0, step_reach))
        shoulder_angle = math.asin(step_reach)

        return shoulder_angle, knee_angle
```
The math isn't very advanced but you need to take your time to assimilate it<br>

#### 3.3 - IK gait
```
 def get_ik_gait(self, t, phase_offset, step_scale):
        T = 0.80
        duty_factor = 0.60
        cycle_progress = ((t / T) + phase_offset) % 1.0

        # --- SPIDER GAIT SETTINGS ---
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

#### 3.4 - Odom
```
        speed_multiplier = xx

        self.odom_x += (
            self.cmd_x * self.speed_multiplier * math.cos(self.odom_yaw)
        ) * self.dt
        self.odom_y += (
            self.cmd_x * self.speed_multiplier * math.sin(self.odom_yaw)
        ) * self.dt
```
The you just have to publish it to /odom<br>
<br>
One of the many chalenges of making a walking robot is friction and foot slippage. Even in simulation, the robot rarely moves exactly as commanded, causing odometry to not represent the real robot position. To compensate it we will use our IMU in combination of our speed_multiplier


Now we will try to make the robot [move](https://github.com/joschmaCYU/quadruped#teleoperation)
