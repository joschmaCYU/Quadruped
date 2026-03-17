#!/usr/bin/env python3
import rclpy

from std_msgs.msg import Float32MultiArray
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Header
import math
import time

class QuadrupedIKNode(Node):
    def __init__(self):
        super().__init__('quadruped_ik_node')
        # Publish to the standard joint_states topic that RViz listens to
        self.publisher_ = self.create_publisher(JointState, 'joint_states', 10)
        
        # Run the loop at 20 Hz (every 0.05 seconds)
        self.timer = self.create_timer(0.05, self.timer_callback)
        self.start_time = time.time()
        
        # Your robot's specific measurements (in meters) extracted from the URDF
        self.L1 = 0.1845
        self.L2 = 0.2500

        self.get_logger().info("Quadruped IK Node started! Moving legs...")

    def calculate_ik(self, x_target, z_target):
        """
        Calculates the shoulder and knee angles for a given target foot position (x, z).
        """
        # Distance squared from shoulder to target foot position
        D_squared = x_target**2 + z_target**2
        
        # Check if target is physically reachable to prevent math domain crashes
        if D_squared > (self.L1 + self.L2)**2 or D_squared < (self.L1 - self.L2)**2:
            self.get_logger().warn("Target out of reach!")
            return 0.0, 0.0 
            
        # Calculate Knee Angle (Theta 2)
        # Using negative sqrt to make the knee bend backwards like a dog
        cos_theta2 = (D_squared - self.L1**2 - self.L2**2) / (2 * self.L1 * self.L2)
        theta2 = math.atan2(-math.sqrt(1 - cos_theta2**2), cos_theta2) 
        
        # Calculate Shoulder Angle (Theta 1)
        theta1 = math.atan2(z_target, x_target) - math.atan2(self.L2 * math.sin(theta2), self.L1 + self.L2 * math.cos(theta2))
        
        return theta1, theta2

    def get_trajectory(self, t, phase_offset):
        """
        Calculates a semi-elliptical walking trajectory.
        phase_offset: 0.0 for Pair A, 0.5 for Pair B (to keep them alternating)
        """
        # How long one full step cycle takes in seconds (lower = faster walking)
        T = 1.0 
        
        # Calculate exactly where we are in the cycle (from 0.0 to 1.0)
        cycle_progress = ((t / T) + phase_offset) % 1.0
        
        # Your step settings
        stride_length = 0.08  # 8cm total stride (4cm forward, 4cm back)
        step_height = 0.04    # 4cm lift in the air
        resting_z = -0.25     # How low the robot crouches
        
        half_stride = stride_length / 2.0
        
        if cycle_progress < 0.5:
            # --- STANCE PHASE (Foot on the ground) ---
            # Progress scales from 0.0 to 1.0 during this half
            stance_p = cycle_progress / 0.5 
            
            # X moves smoothly backward from front to back
            x = half_stride - (stride_length * stance_p)
            # Z stays perfectly flat!
            z = resting_z
        else:
            # --- SWING PHASE (Foot in the air) ---
            # Progress scales from 0.0 to 1.0 during this half
            swing_p = (cycle_progress - 0.5) / 0.5 
            
            # X moves smoothly forward from back to front
            x = -half_stride + (stride_length * swing_p)
            # Z arcs upward using a sine wave
            z = resting_z + step_height * math.sin(swing_p * math.pi)
            
        return x, z

    def timer_callback(self):
        t = time.time() - self.start_time
        
        # --- TRAJECTORY GENERATION ---
        # Pair A and Pair B are exactly half a cycle (0.5) apart
        x_A, z_A = self.get_trajectory(t, 0.0)
        x_B, z_B = self.get_trajectory(t, 0.5)

        # --- CALCULATE ANGLES ---
        theta1_A, theta2_A = self.calculate_ik(x_A, z_A)
        theta1_B, theta2_B = self.calculate_ik(x_B, z_B)

        # --- TUNE YOUR RESTING POSE OFFSETS HERE ---
        shoulder_offset = 0.0 
        knee_offset = math.pi / 2 
        
        # --- CONSTRUCT ROS 2 MESSAGE ---
        msg = JointState()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        
        msg.name = [
            'base_link_to_cube5', 'cube5_to_cube9',   # Front Left
            'base_link_to_cube6', 'cube6_to_cube10',  # Back Right
            'base_link_to_cube7', 'cube7_to_cube11',  # Front Right
            'base_link_to_cube8', 'cube8_to_cube12'   # Back Left
        ]
        
        # Apply the offsets to the calculated angles
        msg.position = [
            theta1_A + shoulder_offset, theta2_A + knee_offset,  # Front Left 
            theta1_A + shoulder_offset, theta2_A + knee_offset,  # Back Right 
            theta1_B + shoulder_offset, theta2_B + knee_offset,  # Front Right
            theta1_B + shoulder_offset, theta2_B + knee_offset   # Back Left  
        ]
        
        # Publish the message
        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = QuadrupedIKNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
