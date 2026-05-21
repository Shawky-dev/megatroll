#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from megajaw_brain.utils import clip_num
from megajaw_interfaces.msg import TargetControl

STATES = {
    IDLE: 0,
    TO_TARGET: 1,
    GRIPPER_CLOSE: 2,
    GO_HOME: 3,
    GRIPPER_OPEN: 4,
}

class ToTargetControllerNode(Node):
    def __init__(self):
        super().__init__("to_target_controller_node")
        self.get_logger().info(f"to_target_controller_node Started")

        self.declare_parameter("is_autonomous", True)
        self.is_autonomous = self.get_parameter("is_autonomous").value

        self.W_MAX = 1
        self.KW = self.W_MAX

        self.GAMMA = 1.3
        self.V_MAX = 0.7
        
        self.state = STATES["IDLE"]
        
        # self.gripper_pub = self.create_publisher(Bool, "/cmd_grip", 10)
        self.create_timer(0.1, self.main_loop)

    def main_loop(self):
        if self.state == STATES["IDLE"]:
            self.idle()
        elif self.state == STATES["TO_TARGET"]:
            pass
        elif self.state == STATES["GRIPPER_CLOSE"]:
            pass
        elif self.state == STATES["GO_HOME"]:
            pass
        elif self.state == STATES["GRIPPER_OPEN"]:
            pass
        
        
    def idle(self):
        # Open Gripper
        
    def move_to_target(self, msg: TargetControl):
        if not self.is_autonomous:
            return

        w = clip_num(self.KW * msg.err_x, -self.W_MAX, self.W_MAX)
        v = clip_num(self.V_MAX * (1 - abs(msg.err_x)) ** self.GAMMA, -self.V_MAX, self.V_MAX)


def main(args=None):
    rclpy.init(args=args)
    node = ToTargetControllerNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
