from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    package_name = 'quadruped_basics'

    return LaunchDescription([
        # Start the Python Brain Node
        Node(
            package='quadruped_basics',
            executable='brain.py',
            name='brain_node',
            output='screen',
            emulate_tty=True, # Ensures color output in the console
        ),
        # Start the C++ Actuator Node
        Node(
            package='quadruped_basics',
            executable='actuator_node',
            name='actuator_node',
            output='screen',
            emulate_tty=True,
        )
    ])
