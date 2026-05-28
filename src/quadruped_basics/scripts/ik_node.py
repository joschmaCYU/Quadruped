#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray, Bool
from geometry_msgs.msg import Twist, TransformStamped
from tf2_ros import TransformBroadcaster
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
from rclpy.qos import qos_profile_sensor_data
import math


class GazeboQuadrupedNode(Node):
    def __init__(self):
        super().__init__("gazebo_quadruped_node")
        self.publisher_ = self.create_publisher(
            Float64MultiArray, "/joint_group_position_controller/commands", 10
        )
        self.subscription = self.create_subscription(
            Twist, "cmd_vel", self.cmd_vel_callback, 10
        )

        self.odom_pub = self.create_publisher(Odometry, "/odom", 10)

        self.dashboard_override = False
        self.override_sub = self.create_subscription(
            Bool, "/dashboard_override", self.override_callback, 10
        )

        self.imu_sub = self.create_subscription(
            Imu, "/imu", self.imu_callback, qos_profile_sensor_data
        )

        self.tf_broadcaster = TransformBroadcaster(self)
        self.odom_x = 0.0
        self.odom_y = 0.0
        self.odom_yaw = 0.0

        self.cmd_x = 0.0
        self.cmd_w = 0.0

        self.walk_time = 0.0
        self.dt = 0.05
        self.timer = self.create_timer(self.dt, self.timer_callback)

        if not self.has_parameter("use_sim_time"):
            self.declare_parameter("use_sim_time", False)
        is_sim = self.get_parameter("use_sim_time").value

        if is_sim:
            self.get_logger().info("Using GAZEBO SIMULATION multipliers")
            self.speed_multiplier = 0.08247
        else:
            self.get_logger().info("Using REAL HARDWARE multipliers")
            self.speed_multiplier = 0.08247

        self.get_logger().info("Spider Brain Online! Waiting for commands...")

    def imu_callback(self, msg):
        q = msg.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.odom_yaw = math.atan2(siny_cosp, cosy_cosp)
        self.actual_turn_speed = msg.angular_velocity.z

    def override_callback(self, msg):
        self.dashboard_override = msg.data

    def cmd_vel_callback(self, msg):
        self.cmd_x = msg.linear.x
        self.cmd_w = msg.angular.z

    def calculate_ik(self, x, z):
        L1 = 0.206
        L2 = 0.250

        # FIX 1: Limite augmentée pour ne pas bloquer la hauteur de marche
        z = max(z, -0.26)
        z = min(z, 0.0)

        cos_knee = abs(z) / L2
        cos_knee = max(0.0, min(1.0, cos_knee))
        knee_angle = math.acos(cos_knee)

        horizontal_reach = L1 + (L2 * math.sin(knee_angle))

        step_reach = x / horizontal_reach
        step_reach = max(-1.0, min(1.0, step_reach))
        shoulder_angle = math.asin(step_reach)

        return shoulder_angle, knee_angle

    def get_ik_gait(self, t, phase_offset, step_scale):
        T = 0.80
        duty_factor = 0.60
        cycle_progress = ((t / T) + phase_offset) % 1.0

        stride_length = 0.25
        step_height = 0.08

        # FIX 2: Hauteur unifiée entre l'arrêt et la marche
        stand_height = -0.22

        # FIX 3: Hauteur de pas dynamique !
        # Si le robot fait un tout petit pas (ex: marche arrière lente), il lève moins haut la patte.
        actual_step_height = step_height * min(1.0, max(0.2, abs(step_scale)))

        if cycle_progress < duty_factor:
            # STANCE PHASE
            stance_p = cycle_progress / duty_factor
            target_x = (stride_length / 2.0) - (stride_length * stance_p)
            target_z = stand_height
        else:
            # SWING PHASE
            swing_p = (cycle_progress - duty_factor) / (1.0 - duty_factor)
            target_x = -(stride_length / 2.0) + (stride_length * swing_p)
            target_z = stand_height + (actual_step_height * math.sin(swing_p * math.pi))

        target_x = target_x * step_scale

        return self.calculate_ik(target_x, target_z)

    def timer_callback(self):
        if self.cmd_x != 0.0 or self.cmd_w != 0.0:
            self.walk_time += self.dt
        else:
            self.walk_time = 0.0  # Réinitialise le cycle quand on s'arrête proprement

        self.odom_x += (
            self.cmd_x * self.speed_multiplier * math.cos(self.odom_yaw)
        ) * self.dt
        self.odom_y += (
            self.cmd_x * self.speed_multiplier * math.sin(self.odom_yaw)
        ) * self.dt

        # --- TF BROADCASTER ---
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = "odom"
        t.child_frame_id = "base_footprint"

        t.transform.translation.x = self.odom_x
        t.transform.translation.y = self.odom_y
        t.transform.translation.z = 0.0

        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = math.sin(self.odom_yaw / 2.0)
        t.transform.rotation.w = math.cos(self.odom_yaw / 2.0)

        self.tf_broadcaster.sendTransform(t)

        # --- ODOMETRY PUBLISHER ---
        odom_msg = Odometry()
        odom_msg.header.stamp = t.header.stamp
        odom_msg.header.frame_id = "odom"
        odom_msg.child_frame_id = "base_footprint"

        odom_msg.pose.pose.position.x = self.odom_x
        odom_msg.pose.pose.position.y = self.odom_y
        odom_msg.pose.pose.orientation = t.transform.rotation

        odom_msg.twist.twist.linear.x = self.cmd_x * self.speed_multiplier
        odom_msg.twist.twist.angular.z = getattr(self, "actual_turn_speed", 0.0)

        self.odom_pub.publish(odom_msg)

        # --- KINEMATICS ---
        is_moving = self.cmd_x != 0.0 or self.cmd_w != 0.0
        msg = Float64MultiArray()

        if not is_moving:
            # IDLE STATE: Snap to unified standing pose
            stand_height = -0.22
            idle_shoulder, idle_knee = self.calculate_ik(0.0, stand_height)
            msg.data = [
                float(idle_shoulder),
                float(idle_knee),  # FL
                float(-idle_shoulder),
                float(idle_knee),  # BR (Mirrored)
                float(-idle_shoulder),
                float(idle_knee),  # FR (Mirrored)
                float(idle_shoulder),
                float(idle_knee),  # BL
            ]
        else:
            amp_FL = self.cmd_x - (self.cmd_w * 1.5)
            amp_FR = self.cmd_x + (self.cmd_w * 1.5)
            amp_BL = self.cmd_x - (self.cmd_w * 1.5)
            amp_BR = self.cmd_x + (self.cmd_w * 1.5)

            shoulder_FL, knee_FL = self.get_ik_gait(self.walk_time, 0.0, amp_FL)
            shoulder_BR, knee_BR = self.get_ik_gait(self.walk_time, 0.0, amp_BR)

            shoulder_FR, knee_FR = self.get_ik_gait(self.walk_time, 0.5, amp_FR)
            shoulder_BL, knee_BL = self.get_ik_gait(self.walk_time, 0.5, amp_BL)

            msg.data = [
                float(shoulder_FL),
                float(knee_FL),  # Front Left
                float(-shoulder_BR),
                float(knee_BR),  # Back Right
                float(-shoulder_FR),
                float(knee_FR),  # Front Right
                float(shoulder_BL),
                float(knee_BL),  # Back Left
            ]

        if not self.dashboard_override:
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


if __name__ == "__main__":
    main()
