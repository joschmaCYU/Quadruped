# Docker
## Start docker
docker-compose up -d quadruped  
docker-compose up -d 

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

# Freecad :
conda activate freecad_1_0_312 && freecad
conda deactivate

# Pins
## Pair A (These legs move together):
    Front Left Shoulder: Pin 13  
    Front Left Knee: Pin 14  
    Back Right Shoulder: Pin 15  
    Back Right Knee: Pin 16  

## Pair B (These legs move together):
    Front Right Shoulder: Pin 17  
    Front Right Knee: Pin 18  
    Back Left Shoulder: Pin 19  
    Back Left Knee: Pin 23  

# Launch robot :
ros2 launch quadruped_basics display.launch.py

## If robot not connecting :
Do you see your esp and lidar ?  
ls /dev/ttyUSB*  
Is it publishing imu values ?  
ros2 topic info /imu --verbose  
Is ros still running ?  
ros2 daemon stop && ros2 daemon start && ros2 topic list  
Are there multiple instance of micro ros ?  
sudo fuser -v /dev/ttyUSB0 && sudo pkill -9 micro_ros_agent  
Try to connect in an empty container:  
sudo docker run -it --rm -v /dev:/dev --privileged --net=host microros/micro-ros-agent:jazzy serial --dev /dev/ttyUSB0 -v6  

# Launch  sim + robot brain
ros2 launch quadruped_basics sim.amcl.launch.py  
OR  
ros2 launch quadruped_basics sim.slam.launch.py  

### Save map :
ros2 run nav2_map_server map_saver_cli -f /home/ros/ros2_ws/src/quadruped_project/src/quadruped_basics/maps/my_first_map

# Weight :
Foot : 7  
Leg : 4  
MG 90s : 14  
Body : 73  
Lidar : 46  
esp32 : 10  
Battery : 140  
UBEC 6A : 15  
UBEC 3A : 10  

7 * 4 + 4 * 4 + 14 * 8 + 73 + 46 + 10 + 140 + 15 + 10 = 450  
