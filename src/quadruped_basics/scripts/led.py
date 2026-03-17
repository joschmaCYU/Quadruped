#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32

class LedBlinker(Node):
    def __init__(self):
        super().__init__('pc_blinker_node')
        # Create a publisher on the topic '/led_command'
        self.publisher_ = self.create_publisher(Int32, '/my_robot/led_command', 10)
        
        # Create a timer that fires every 1.0 seconds
        self.timer = self.create_timer(1.0, self.timer_callback)
        
        self.led_state = 0 # 0 = OFF, 1 = ON
        self.get_logger().info('Blinker Node Started. Sending commands to ESP32...')

    def timer_callback(self):
        # Toggle the state
        self.led_state = 1 if self.led_state == 0 else 0
        
        # Create and send the message
        msg = Int32()
        msg.data = self.led_state
        self.publisher_.publish(msg)
        
        state_str = "ON" if self.led_state == 1 else "OFF"
        self.get_logger().info(f'Published: Turn LED {state_str}')

def main(args=None):
    rclpy.init(args=args)
    blinker = LedBlinker()
    try:
        rclpy.spin(blinker)
    except KeyboardInterrupt:
        pass
    finally:
        blinker.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
