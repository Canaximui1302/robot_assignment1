# draw_square_server.py
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from turtle_square_interfaces.action import DrawSquare
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
import math

class DrawSquareServer(Node):
    def __init__(self):
        super().__init__('draw_square_server')

        self._cmd_vel_pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self._pose = None
        self.create_subscription(Pose, '/turtle1/pose', self.pose_callback, 10)
        self._feedback = DrawSquare.Feedback()
        # create action server
        self._action_server = ActionServer(
            self,
            DrawSquare,          # action type
            '/draw_square',      # action name
            self.execute_callback 
        )

        self.get_logger().info("DrawSquareServer node created and ActionServer initialized")

    def execute_callback(self, goal_handle):
        side = goal_handle.request.side_length
        speed = goal_handle.request.speed

        self.get_logger().info(f"Received goal: side={side}, speed={speed}")

        total_distance = side * 4
        remaining_distance = total_distance

        for i in range(4):
            # Move forward one side
            self.get_logger().info(f"Moving side {i+1}")
            self.move_forward(side, speed)

            # Update and publish feedback
            remaining_distance -= side
            self._feedback.remaining_distance = remaining_distance
            goal_handle.publish_feedback(self._feedback)
            self.get_logger().info(f"Remaining distance: {remaining_distance}")

            # Rotate 90 degrees
            self.get_logger().info(f"Rotating after side {i+1}")
            self.rotate_90(1.)

        # Goal completed
        goal_handle.succeed()
        result = DrawSquare.Result()
        result.success = True
        self.get_logger().info("Goal completed: turtle completed the square!")
        return result

    def pose_callback(self, msg):
        """Save the latest turtle pose."""
        self._pose = msg

    def move_forward(self, distance, speed):
        """Move the turtle forward by 'distance' meters at 'speed'."""
        if self._pose is None:
            self.get_logger().warn("No pose yet cannot move")
            return

        init_x = self._pose.x
        init_y = self._pose.y

        twist = Twist()
        twist.linear.x = speed
        traveled = 0.0

        while traveled < distance and rclpy.ok():
            self._cmd_vel_pub.publish(twist)
            rclpy.spin_once(self)
            dx = self._pose.x - init_x
            dy = self._pose.y - init_y
            traveled = math.sqrt(dx**2 + dy**2)

        # stop the turtle
        twist.linear.x = 0.0
        self._cmd_vel_pub.publish(twist)

    def rotate_90(self, speed):
        """Rotate the turtle 90 degrees clockwise at a given angular speed."""
        if self._pose is None:
            self.get_logger().warn("No pose yet cannot rotate")
            return

        twist = Twist()
        twist.angular.z = float(speed)

        rotated = 0.0
        last_angle = self._pose.theta
        curr_angle = self._pose.theta

        target_angle = (math.pi/2) - 0.05 # minus some small constant due to bad delay

        while rotated < target_angle and rclpy.ok():
            self._cmd_vel_pub.publish(twist)
            rclpy.spin_once(self)
            curr_angle = self._pose.theta
            rotated += abs(curr_angle - last_angle)
            last_angle = curr_angle

        twist.angular.z = 0.0
        self._cmd_vel_pub.publish(twist)
        

def main():
    rclpy.init()
    node = DrawSquareServer()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
