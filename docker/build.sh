#!/bin/bash

# Get the absolute path of the directory containing this script (docker directory)
SCRIPT_PATH=$(dirname $(realpath "$0"))

# Get the parent directory path 
# This is where our actual ROS 2 package code lives
PARENT_PATH=$(dirname "$SCRIPT_PATH")

check_and_install_docker()
{
    if ! command -v docker &> /dev/null; then
        LOG="Docker is not installed. Downloading and installing Docker..."
        print_debug
        
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        
        # Clean up the installation script
        rm get-docker.sh
        
        LOG="Docker installation complete!"
        print_debug
    else
        LOG="Docker is already installed. Proceeding..."
        print_debug
    fi
}

# Function to build the Docker image
build_docker_image()
{
    LOG="Building Docker image manipulation:latest ..."
    print_debug

    # Build the Docker image
    # -f $SCRIPT_PATH/Dockerfile: Specify the path to the Dockerfile in the docker directory
    # -t manipulation:latest: Tag the image as manipulation:latest
    # $PARENT_PATH: Use the parent directory as the build context, allowing access to all package files
    # --no-cache: Build the image without using the cache, ensuring fresh dependencies
    sudo docker image build -f $SCRIPT_PATH/Dockerfile -t manipulation:latest $PARENT_PATH --no-cache
}

# Function to print debug messages
print_debug()
{
    echo ""
    echo $LOG
    echo ""
}

# Main execution flow

# To build for arm
# sudo docker buildx build --platform linux/arm64 -f Dockerfile -t manipulation:latest /home/josch/ros2_ws/src/quadruped/ --no-cache --load
# To activate emulation 
# sudo docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

check_and_install_docker
build_docker_image
