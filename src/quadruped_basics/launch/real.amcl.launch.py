import os
from launch.actions import TimerAction
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    pkg_name = "quadruped_basics"

    # Path to URDF
    urdf_path = os.path.join(
        get_package_share_directory(pkg_name), "urdf", "quad.urdf.xacro"
    )

    # Process Xacro
    robot_description = ParameterValue(Command(["xacro ", urdf_path]), value_type=str)

    # 1. Robot State Publisher
    rsp_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"robot_description": robot_description}],
        output="screen",
    )

    # 2. Python IK Node
    ik_node = Node(
        package=pkg_name,
        executable="ik_node.py",
        name="quadruped_ik_node",
        output="screen",
        parameters=[{"use_sim_time": False}],
    )

    # sudo pkill -9 micro_ros_agent
    kill_process = ExecuteProcess(
        cmd=["pkill", "-9", "micro_ros_agent"], output="screen"
    )

    # 3. Micro-ROS Agent via Docker
    microros_agent_process = ExecuteProcess(
        cmd=[
            "sudo",
            "docker",
            "run",
            "--rm",
            "-v",
            "/dev:/dev",
            "--privileged",
            "--net=host",
            "microros/micro-ros-agent:jazzy",
            "serial",
            "--dev",
            "/dev/ttyUSB0",
        ],
        output="screen",
    )

    # 4. LiDAR Driver
    ldlidar_node = Node(
        package="ldlidar_stl_ros2",
        executable="ldlidar_stl_ros2_node",
        name="LD19",
        output="screen",
        parameters=[
            {"product_name": "LDLiDAR_LD19"},
            {"topic_name": "scan"},
            {"frame_id": "base_laser"},
            {"port_name": "/dev/ttyUSB1"},
            {"port_baudrate": 230400},
            {"laser_scan_dir": True},
            {"enable_angle_crop_func": False},
        ],
    )

    # 5. LiDAR TF Offset
    base_link_to_laser_tf_node = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="base_link_to_base_laser_ld06",
        arguments=[
            "--x",
            "0",
            "--y",
            "0",
            "--z",
            "0.18",
            "--roll",
            "0",
            "--pitch",
            "0",
            "--yaw",
            "0",
            "--frame-id",
            "base_footprint",
            "--child-frame-id",
            "base_laser",
        ],
    )

    # 6. RViz2
    nav2_rviz_config_path = os.path.join(
        get_package_share_directory("nav2_bringup"), "rviz", "nav2_default_view.rviz"
    )

    nav2_rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", nav2_rviz_config_path],
        parameters=[{"use_sim_time": False}],
        output="screen",
    )

    # 7. AMCL + Nav2 Bringup (Replaces Navigation + SLAM)
    nav2_launch_path = os.path.join(
        get_package_share_directory("nav2_bringup"), "launch", "bringup_launch.py"
    )

    nav2_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(nav2_launch_path),
        launch_arguments={
            "use_sim_time": "false",  # Must be false for real hardware
            "map": "/home/ros/ros2_ws/src/quadruped_basics/maps/third_better_map.yaml",
            "params_file": "/home/ros/ros2_ws/src/quadruped_basics/config/my_nav2.yaml",
            "cmd_vel_topic": "cmd_vel",  # Bypass multiplexer
            "use_velocity_smoother": "False",  # Prevent 0.0 spam
            "use_collision_monitor": "False",  # Prevent 0.0 spam
        }.items(),
    )

    delayed_nav2_cmd = TimerAction(period=5.0, actions=[nav2_cmd])

    return LaunchDescription(
        [
            rsp_node,
            ik_node,
            nav2_rviz_node,
            ldlidar_node,
            base_link_to_laser_tf_node,
            kill_process,
            microros_agent_process,
            delayed_nav2_cmd,
        ]
    )
