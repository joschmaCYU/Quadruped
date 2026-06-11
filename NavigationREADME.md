# Navigation (SLAM & AMCL)
In the ROS 2 world, it’s not a battle of "SLAM vs. AMCL" **they work together** as a team to give your robot a true understanding of its environment.

## 1. SLAM (simultaneous localization and mapping)
**What is it?** SLAM is the process of a robot building a map of an unknown environment while simultaneously keeping track of its current location within that map.
**How to use it:** You use SLAM in "Explore" mode. Manually drive your quadruped around your room. The LiDAR scans the walls and draws a map. Once the map is complete, save it as a static image file (`.yaml`) and turn SLAM off entirely.

```
ros2 run nav2_map_server map_saver_cli -f my_room_map
```

## 2. AMCL (Adaptive Monte Carlo Localization)
Once you have a saved map, switch to AMCL for day-to-day autonomous navigation. AMCL scatters a cloud of guesses (particles) on your map and uses the live LiDAR data to lock onto the robot's exact position.

[!TIP]
> If you do not know your environment, you must use both at the same time. You launch slam_toolbox so the robot can "see" and build the walls dynamically, and you launch Nav2 so the robot can plan paths.

[!TIP]
> AMCL is highly recommended for walking robots. Quadrupeds suffer from "foot slip" which causes the odometry to drift. If you run SLAM permanently, this slipping will slowly warp and duplicate your walls, corrupting your map. AMCL uses a locked, read-only map and simply corrects the robot's position against it. Use SLAM for unknown environments, and AMCL for daily operation.

## 3. Configuration files
Both AMCL and SLAM require highly tuned parameters to work perfectly.
Grab the custom configurations from this repo:
```
cd ~/ros2_ws/src/quadruped/config
wget [https://raw.githubusercontent.com/joschmaCYU/quadruped/main/src/quadruped_basics/config/my_slam_params.yaml](https://raw.githubusercontent.com/joschmaCYU/quadruped/main/src/quadruped_basics/config/my_slam_params.yaml)
wget [https://raw.githubusercontent.com/joschmaCYU/quadruped/main/src/quadruped_basics/config/my_nav2.yaml](https://raw.githubusercontent.com/joschmaCYU/quadruped/main/src/quadruped_basics/config/my_nav2.yaml)
```

## Roadblocks & solutions: navigation tuning
Getting Nav2 and SLAM to respect a custom quadruped geometry required solving some heavy TF and costmap conflicts.

### The things to configure
#### For Nav2
- robot_radius
- inflation_radius: size of the invisible "danger zone" around walls
- vx_min and vx_max: how fast or slow will your robot move. 

#### For Slam
- minimum_travel_distance and minimum_travel_heading: because a quadruped shuffles with small steps, lowering these thresholds forces SLAM to update the map constantly

### The "ghost wall" (Nav2 paralyzed)
**The problem**: the robot would freeze and refuse to move if an obstacle to close. The MPPI controller was aborting all trajectories.
<br>
**The fix**: first verify your robot_radius. I had to adjust mine to 0.08 (6 cm actual radius + 2 cm safety buffer) **in both the local_costmap and global_costmap**. I also drastically reduced the inflation_radius from 0.7 to 0.2 so the planner wouldn't treat narrow doorways as solid walls.

### The spinning room (TF tree inversion)
**The problem**: In RViz, when the physical robot turned, the robot model stayed still and the LiDAR points (the walls of the room) spun around it.
<br>
**The Fix**: this was a TF conflict.
1) In my_nav2.yaml, the robot_base_frame was mistakenly set to base_link instead of base_footprint.
2) Verify that your IMU is connected and that it's publishing.
