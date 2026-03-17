#!/bin/bash
set -e

# Setup ROS 2 Environment
source /opt/ros/jazzy/setup.bash
source /home/ros/ros2_ws/install/setup.bash

# Setup Domain ID if shared folder exists
SHARED_ROS2="/home/ros/shared/ros2"
ROS_DOMAIN_ID_FILE="$SHARED_ROS2/ros_domain_id.txt"

if [ -d "$SHARED_ROS2" ]; then
    if [ ! -f "$ROS_DOMAIN_ID_FILE" ]; then
        echo "0" > "$ROS_DOMAIN_ID_FILE"
    fi
    export ROS_DOMAIN_ID=$(cat "$ROS_DOMAIN_ID_FILE")
    # echo "ROS_DOMAIN_ID set to $ROS_DOMAIN_ID"
fi

# Execute the command passed into this entrypoint
exec "$@"
