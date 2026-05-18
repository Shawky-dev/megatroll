#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped
import serial
import time

class UartBridgeNode(Node):
    def __init__(self):
        super().__init__('uart_bridge_node')
        
        # ===== UART CONFIG =====
        self.serial_port = '/dev/ttyAMA0'  # Raspberry Pi hardware UART
        self.baud_rate = 115200
        self.timeout = 0.1
        
        # Try to open serial port
        try:
            self.ser = serial.Serial(
                self.serial_port, 
                self.baud_rate, 
                timeout=self.timeout
            )
            time.sleep(2)  # Wait for STM32 to reset
            self.get_logger().info(f"✅ UART connected: {self.serial_port} @ {self.baud_rate}")
            self.uart_connected = True
        except serial.SerialException as e:
            self.get_logger().error(f"❌ Failed to open UART: {e}")
            self.get_logger().error("💡 Tips:")
            self.get_logger().error("  1. Run: sudo raspi-config → Interface Options → Serial → Disable login shell, enable hardware serial")
            self.get_logger().error("  2. Add user to dialout group: sudo usermod -a -G dialout $USER (then reboot)")
            self.get_logger().error("  3. Check port: ls -l /dev/ttyAMA* /dev/ttyUSB*")
            self.uart_connected = False
            self.ser = None
        
        # ===== ROS2 SUBSCRIBER =====
        # Subscribe to /cmd_vel (handles both Twist and TwistStamped)
        self.subscription = self.create_subscription(
            TwistStamped,  # Your web UI publishes TwistStamped
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )
        # Fallback subscription for plain Twist (optional)
        self.subscription_plain = self.create_subscription(
            Twist,
            '/cmd_vel_raw',  # Optional alternate topic
            self.cmd_vel_callback_plain,
            10
        )
        
        self.get_logger().info("🎮 UART Bridge Node started – waiting for /cmd_vel...")
    
    def cmd_vel_callback(self, msg: TwistStamped):
        """Handle TwistStamped messages from web joystick"""
        if not self.uart_connected:
            return
        
        linear_x = msg.twist.linear.x
        angular_z = msg.twist.angular.z
        
        # DEBUG: Print what we received
        self.get_logger().debug(f"📥 Received: linear.x={linear_x:.2f}, angular.z={angular_z:.2f}")
        
        # For now: just send a test character to verify UART works
        # We'll replace this with real motor logic in Step 6
        self.send_to_stm32(b'T')  # 'T' = Test
    
    def cmd_vel_callback_plain(self, msg: Twist):
        """Handle plain Twist messages (fallback)"""
        if not self.uart_connected:
            return
        self.send_to_stm32(b'T')
    
    def send_to_stm32(self, data: bytes):
        """Send bytes over UART to STM32"""
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(data)
                self.get_logger().info(f"📤 Sent to STM32: {data}")
            except serial.SerialException as e:
                self.get_logger().error(f"❌ UART write failed: {e}")
                self.uart_connected = False
    
    def destroy_node(self):
        """Cleanup: stop motors and close UART"""
        if self.ser and self.ser.is_open:
            self.ser.write(b'X')  # Send STOP command
            self.ser.close()
            self.get_logger().info("🔌 UART closed")
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = UartBridgeNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("🛑 Shutting down...")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
