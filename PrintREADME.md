### 2 - Bringing it to your computer
#### 2.1 - Getting the idea
So you want to design your robot, I have a few tips for you.<br>
Beggin by (and I strongly advise you to do so) take a pencil and a sheet of paper and try to draw your robot!

My sketches:
<img width="644" height="466" alt="Autre (19)" src="https://github.com/user-attachments/assets/6e8cc93c-b071-4589-9d92-290925689307" />
<br>

This will help you refine your idea. You will have to ask yourself many questions about how it will move, its height, its length, etc.<br>
You can take inspiration from other robots! I took great inspiration of [sesame-robot](https://github.com/dorianborian/sesame-robot/tree/main).
> [!WARNING]
> There are multiple types of walking robots, bipedal (2 legs), qudruped, hexapod ect...
> There are 2 general type of leg position: mammalian and reptilian.

For mammalian the legs are under the body, like a horse or a dog.<br>
For reptilian the legs are on the side, like a spider or a crocodile (that's what I went with)
<br>
> [!TIP]
> Because the MG90S servos are weak, the chassis must be as lightweight as possible.
My robot walks like a spider robot. It has 8-DOF.

#### 2.2 - The design
Now this is the part where you have to take your sketchs and make them in a CAD. Iterate as many time until you are satisfied. *No need to print it yet.*<br>
<br>
My cad robot:
<img width="428" height="364" alt="Screenshot_20260508_143424" src="https://github.com/user-attachments/assets/9bc27b7e-f8cc-4328-8bc1-0c3a4d382001" />


#### 2.3 - Creating my urdf file
##### 2.3.1 - What is an urdf file ?
It's simple! It's a file that describes your robot. This file will be used by your simulation software to make the robot move. Rather then having just a fixed 3d the urdf file specifies how parts move/rotate along side each other.
##### 2.3.2 - How to make it
Either you rebuild your robot in an urdf software like [D-Robotics](https://urdf.d-robotics.cc) or [Lever Robotics](https://lever-robotics.github.io/URDF_creator/). This can be done quick and dirty but can be less precise.<br>
Or you use your newly modeled robot to genereate it. [Here](https://docs.ros.org/en/humble/Tutorials/Intermediate/URDF/Exporting-an-URDF-File.html) is a tutorial for ROS on how to export your CAD file to an URDF file.
> [!TIP]
> You will have to specifyl how each part move/rotates this can be tidius but you will have the exact replicate of your robot in the sim !

Speaking of [sim](https://github.com/joschmaCYU/quadruped#3---simulating-the-robot)
