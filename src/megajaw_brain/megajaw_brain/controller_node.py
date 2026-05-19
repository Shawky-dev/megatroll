#!/usr/bin/env python3

import math
import time
import serial

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


class CmdVelUartBridge(Node):
    def __init__(self):
        super().__init__('cmd_vel_uart_bridge')

        # Params
        self.declare_parameter('port', '/dev/ttyAMA0')
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('wheel_separation', 0.18)   # meters
        self.declare_parameter('max_linear_speed', 0.5)     # m/s at 100%
        self.declare_parameter('timeout_s', 0.2)

        port = self.get_parameter('port').value
        baudrate = int(self.get_parameter('baudrate').value)
        self.wheel_separation = float(self.get_parameter('wheel_separation').value)
        self.max_linear_speed = float(self.get_parameter('max_linear_speed').value)
        self.timeout_s = float(self.get_parameter('timeout_s').value)

        self.ser = serial.Serial(port, baudrate, timeout=0.02)
        self.last_cmd_time = time.time()

        self.sub = self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_cb, 10)
        self.watchdog = self.create_timer(0.05, self.watchdog_cb)

        self.get_logger().info(f'UART bridge ready on {port} @ {baudrate}')

    def cmd_vel_cb(self, msg: Twist):
        v = float(msg.linear.x)
        w = float(msg.angular.z)

        # Differential-drive mixing
        left = v - (w * self.wheel_separation / 2.0)
        right = v + (w * self.wheel_separation / 2.0)

        # Convert to signed PWM in range [-255, 255]
        left_pwm = int(clamp(round((left / self.max_linear_speed) * 255), -255, 255))
        right_pwm = int(clamp(round((right / self.max_linear_speed) * 255), -255, 255))

        packet = f"M,{left_pwm},{right_pwm}\n"
        self.ser.write(packet.encode('ascii'))
        self.last_cmd_time = time.time()

    def watchdog_cb(self):
        if time.time() - self.last_cmd_time > self.timeout_s:
            self.ser.write(b"M,0,0\n")


def main(args=None):
    rclpy.init(args=args)
    node = CmdVelUartBridge()
    try:
        rclpy.spin(node)
    finally:
        try:
            node.ser.write(b"M,0,0\n")
            node.ser.close()
        except Exception:
            pass
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
