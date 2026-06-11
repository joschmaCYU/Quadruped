ARG ROS_DISTRO=jazzy
FROM ros:${ROS_DISTRO}-ros-base
ARG TARGETARCH

# 1. Install System Dependencies & Tools
RUN apt-get update -q && \
    apt-get install -yq --no-install-recommends \
    tree \
    build-essential \
    git \
    wget \
    curl \
    nano \
    vim \
    neovim \
    lsb-release \
    gnupg2 \
    python3-pip \
    python3-rosdep \
    python3-colcon-common-extensions \
    python3-vcstool \
    software-properties-common \
    ros-${ROS_DISTRO}-ros2-control \
    ros-${ROS_DISTRO}-ros2-controllers \
    ros-${ROS_DISTRO}-teleop-twist-keyboard \
    ros-${ROS_DISTRO}-xacro \
    ros-${ROS_DISTRO}-slam-toolbox \
    ros-${ROS_DISTRO}-navigation2 \
    ros-${ROS_DISTRO}-nav2-bringup \
    && rm -rf /var/lib/apt/lists/*

# Install Heavy Simulation tools ONLY on PC
RUN if [ "$TARGETARCH" = "amd64" ]; then \
        echo "Building for PC (amd64) - Installing Gazebo and RViz..." && \
        apt-get update -q && \
        apt-get install -yq --no-install-recommends \
        ros-${ROS_DISTRO}-desktop \
        ros-${ROS_DISTRO}-ros-gz \
        ros-${ROS_DISTRO}-gz-ros2-control \
        python3-tk \
        python3-matplotlib \
        && rm -rf /var/lib/apt/lists/* ; \
    else \
        echo "Building for Raspberry Pi (arm64) - Skipping heavy simulation tools." ; \
    fi

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# 2. Setup User
ARG USERNAME=ros
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN if id -u $USER_UID >/dev/null 2>&1; then \
        EXISTING_USER=$(getent passwd $USER_UID | cut -d: -f1); \
        echo "User with UID $USER_UID already exists ($EXISTING_USER), reusing it."; \
        if [ "$EXISTING_USER" != "$USERNAME" ]; then \
            usermod -l $USERNAME $EXISTING_USER; \
            groupmod -n $USERNAME $(getent group $USER_GID | cut -d: -f1); \
            usermod -d /home/$USERNAME -m $USERNAME; \
        fi; \
    else \
        groupadd --gid $USER_GID $USERNAME && \
        useradd --uid $USER_UID --gid $USER_GID -m $USERNAME -s /bin/bash; \
    fi \
    && apt-get update && apt-get install -y sudo \
    && echo "$USERNAME ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME \
    && rm -rf /var/lib/apt/lists/*

# 3. Create Workspace & Copy Code
WORKDIR /home/$USERNAME/ros2_ws
RUN chown -R $USERNAME:$USERNAME /home/$USERNAME/ros2_ws
COPY --chown=$USERNAME:$USERNAME src/ /home/$USERNAME/ros2_ws/src/

# 4. Clone Lidar & Micro-ROS Agent into src/
USER root
RUN cd /home/$USERNAME/ros2_ws/src/ && \
    if [ ! -d "ldlidar_stl_ros2" ]; then \
        git clone https://github.com/ldrobotSensorTeam/ldlidar_stl_ros2.git; \
    fi && \
    if [ "${ROS_DISTRO}" = "jazzy" ]; then \
        find ldlidar_stl_ros2 -type f -name log_module.h -exec sed -i 's|//#include <pthread.h>|#include <pthread.h>|g' {} + ; \
    fi && \
    if [ ! -d "micro_ros_setup" ]; then \
        git clone -b ${ROS_DISTRO} https://github.com/micro-ROS/micro_ros_setup.git micro_ros_setup; \
    fi && \
    chown -R $USERNAME:$USERNAME /home/$USERNAME/ros2_ws/src

# Init Rosdep
RUN rosdep init || true && rosdep update
RUN apt-get update && \
    rosdep install --from-paths src --ignore-src -r -y && \
    rm -rf /var/lib/apt/lists/*

# 5. Build Workspace (RAM-Safe Sequential Build)
USER $USERNAME
RUN /bin/bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash && \
    rosdep update && \
    colcon build --packages-select micro_ros_setup --executor sequential && \
    source install/local_setup.bash && \
    ros2 run micro_ros_setup create_agent_ws.sh && \
    ros2 run micro_ros_setup build_agent.sh --executor sequential && \
    colcon build --executor sequential"

# 6. Setup Environment (Bashrc & Aliases)
COPY --chown=$USERNAME:$USERNAME docker/bash_aliases.txt /home/$USERNAME/.bash_aliases
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /home/$USERNAME/.bashrc && \
    echo "source /home/$USERNAME/ros2_ws/install/setup.bash" >> /home/$USERNAME/.bashrc && \
    echo "if [ -f ~/.bash_aliases ]; then . ~/.bash_aliases; fi" >> /home/$USERNAME/.bashrc

# 7. Entrypoint
COPY --chown=$USERNAME:$USERNAME docker/entrypoint.sh /home/$USERNAME/entrypoint.sh
USER root
RUN chmod +x /home/$USERNAME/entrypoint.sh 
USER $USERNAME

ENTRYPOINT ["/home/ros/entrypoint.sh"]
CMD ["/bin/bash"]
