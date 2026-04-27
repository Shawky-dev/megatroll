#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class WebListener(Node):
    def __init__(self):
        super().__init__("web_listener")
        self.get_logger().info(f"web_server_node Started")

        self.subscriber = self.create_subscription(String, '/web_input', self.listener_callback, 10)
        
    def listener_callback(self, msg: String):
        self.get_logger().info(f"we got msg: {msg.data}")


def main(args=None):
    rclpy.init(args=args)
    node = WebListener()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()