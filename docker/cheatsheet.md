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


If ghost topic :
ros2 daemon stop
ros2 daemon start
ros2 topic list

If esp32 not connecting plug the battery after esp32 start
