## Start docker
docker-compose up -d quadruped
## Stop
docker-compose stop quadruped

## Execute commands in docker
docker-compose exec -it quadruped bash

## Activate GUI
xhost +

## Build my docker
bash build.sh

## Remove it 
docker rmi quadruped:latest



ros2 daemon stop
ros2 daemon start
ros2 topic list


ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyUSB0 -v6
