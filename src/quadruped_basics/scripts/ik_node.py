#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray # Gazebo uses 64-bit floats
from geometry_msgs.msg import Twist
import math
import time

class GazeboQuadrupedNode(Node):
    def __init__(self):
        super().__init__('gazebo_quadruped_node')
        
        # 1. Publish to Gazebo's virtual controller
        self.publisher_ = self.create_publisher(Float64MultiArray, '/joint_group_position_controller/commands', 10)
        
        # 2. Listen to the keyboard
        self.subscription = self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 10)
            
        self.current_speed = 0.0 
        self.walk_time = 0.0     
        self.dt = 0.05           
        self.timer = self.create_timer(self.dt, self.timer_callback)
        
        self.L1 = 0.1845
        self.L2 = 0.2500

        self.get_logger().info("Gazebo Brain Online! Waiting for keyboard commands...")

    def cmd_vel_callback(self, msg):
        self.current_speed = msg.linear.x

    def calculate_ik(self, x_target, z_target):
        D_squared = x_target**2 + z_target**2
        if D_squared > (self.L1 + self.L2)**2 or D_squared < (self.L1 - self.L2)**2:
            return 0.0, 0.0 
            
        cos_theta2 = (D_squared - self.L1**2 - self.L2**2) / (2 * self.L1 * self.L2)
        theta2 = math.atan2(-math.sqrt(1 - cos_theta2**2), cos_theta2) 
        theta1 = math.atan2(z_target, x_target) - math.atan2(self.L2 * math.sin(theta2), self.L1 + self.L2 * math.cos(theta2))
        return theta1, theta2

    def get_trajectory(self, t, phase_offset):
# CHANGE THESE THREE LINES:
        T = 0.6               # Faster steps (was 1.0)
        stride_length = 0.08  # Smaller stride (was 0.08)
        step_height = 0.06    # Lower lift to reduce wobble (was 0.04)
        cycle_progress = ((t / T) + phase_offset) % 1.0
        
        resting_z = -0.25     
        half_stride = stride_length / 2.0
        
        if cycle_progress < 0.5:
            stance_p = cycle_progress / 0.5 
            x = half_stride - (stride_length * stance_p)
            z = resting_z
        else:
            swing_p = (cycle_progress - 0.5) / 0.5 
            x = -half_stride + (stride_length * swing_p)
            z = resting_z + step_height * math.sin(swing_p * math.pi)
            
        return x, z

    def timer_callback(self):
        # Only advance the animation if we are commanded to move!
        if self.current_speed != 0.0:
            self.walk_time += (self.dt * self.current_speed)
            
        x_A, z_A = self.get_trajectory(self.walk_time, 0.0)
        x_B, z_B = self.get_trajectory(self.walk_time, 0.5)

        theta1_A, theta2_A = self.calculate_ik(x_A, z_A)
        theta1_B, theta2_B = self.calculate_ik(x_B, z_B)

        shoulder_offset = 0.0 
        knee_offset = math.pi / 2 
        
        # Construct the lightweight array for Gazebo
        msg = Float64MultiArray()
        msg.data = [
            float(theta1_A + shoulder_offset),   float(theta2_A + knee_offset),    # Front Left (Normal)
            float(-(theta1_A + shoulder_offset)), float(-(theta2_A + knee_offset)), # Back Right (FLIPPED!)
            float(-(theta1_B + shoulder_offset)), float(-(theta2_B + knee_offset)), # Front Right (FLIPPED!)
            float(theta1_B + shoulder_offset),   float(theta2_B + knee_offset)     # Back Left (Normal)
        ]
        
        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = GazeboQuadrupedNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
