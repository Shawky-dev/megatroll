#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import serial
import time

class UartTestNode(Node):
    def __init__(self):
        super().__init__('uart_test_node')
        
        # UART CONFIG
        self.port = '/dev/ttyAMA0'
        self.baud = 115200
        
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            time.sleep(2)  # Wait for STM32 to reset
            self.get_logger().info(f'✅ UART connected: {self.port} @ {self.baud}')
        except serial.SerialException as e:
            self.get_logger().error(f'❌ Failed to open UART: {e}')
            self.get_logger().error('💡 Fix: sudo usermod -a -G dialout $USER && reboot')
            self.ser = None
            return

        # Subscribe to test topic
        self.sub = self.create_subscription(
            String, '/uart_test', self.test_callback, 10
        )
        self.get_logger().info('📡 Ready! Publish to /uart_test with data: W, S, A, D, or X')

    def test_callback(self, msg):
        if not self.ser or not self.ser.is_open:
            self.get_logger().warn('UART not connected!')
            return
            
        cmd = msg.data.encode('utf-8')
        self.ser.write(cmd)
        self.get_logger().info(f'📤 Sent to STM32: {cmd}')

    def destroy_node(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = UartTestNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('🛑 Shutting down...')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
