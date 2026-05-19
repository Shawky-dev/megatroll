#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import serial
import time

class UartBlinkNode(Node):
    def __init__(self):
        super().__init__('uart_blink_node')
        
        # UART Setup
        self.port = '/dev/ttyAMA0'
        self.baud = 115200
        
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            time.sleep(2)  # Wait for STM32 to finish boot/reset
            self.get_logger().info('✅ UART connected to STM32')
        except serial.SerialException as e:
            self.get_logger().error(f'❌ Failed to open UART: {e}')
            self.get_logger().error('💡 Fix: sudo usermod -a -G dialout $USER && reboot')
            self.ser = None
            return

        # Subscribe to test topic
        self.sub = self.create_subscription(
            String, '/uart_test', self.cmd_callback, 10)
        self.get_logger().info('📡 Ready! Publish "L" to /uart_test to blink STM32 LED')

    def cmd_callback(self, msg):
        if not self.ser: return
        
        cmd = msg.data.strip().upper()
        if cmd == 'L':
            self.ser.write(b'L')
            self.get_logger().info('📤 Sent "L" → STM32 LED should blink!')

    def destroy_node(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = UartBlinkNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
