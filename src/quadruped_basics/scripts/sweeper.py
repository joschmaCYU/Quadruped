#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32

class ServoSweeper(Node):
    def __init__(self):
        super().__init__('pc_servo_sweeper')
        # Publishing to the exact namespace and topic the ESP32 expects
        self.publisher_ = self.create_publisher(Int32, '/my_robot/servo_cmd', 10)
        self.timer = self.create_timer(2.0, self.timer_callback)
        self.angle = 0
        self.get_logger().info('Sweeper Started. Commanding servo...')

    def timer_callback(self):
        # Toggle between 0 and 180 degrees
        self.angle = 180 if self.angle == 0 else 0
        
        msg = Int32()
        msg.data = self.angle
        self.publisher_.publish(msg)
        self.get_logger().info(f'Published Angle: {self.angle}°')

def main(args=None):
    rclpy.init(args=args)
    node = ServoSweeper()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
