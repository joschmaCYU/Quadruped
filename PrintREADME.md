## 2 - Bringing it to your computer
Now that you know your constrains we can design our robot and I have a few tips for you.<br>

### The Ideation Phase
Beggin by (and I strongly advise you to do so) take a pencil and a `sheet of paper` and try to draw your robot!

My sketches: <br>
<img width="644" height="466" src="https://github.com/user-attachments/assets/6e8cc93c-b071-4589-9d92-290925689307" />
<br>

**This will help you refine your idea**. You will have to ask yourself many questions about how it will move, its height, its length, etc.<br>
You can take inspiration from other robots! I took great inspiration of [sesame-robot](https://github.com/dorianborian/sesame-robot/tree/main).

> [!TIP]
> There are multiple types of walking robots, bipedal (2 legs), quadruped, hexapod ect...  

### Leg configuration
For a quadruped there are 2 general type of leg position: mammalian and reptilian.
- For mammalian the legs are under the body, like a horse or a dog. This is great for forward speed and narrow spaces.
- For reptilian the legs are on the side, like a spider or a crocodile (that's what I went with). This offers excellent stability and a lower center of gravity.

It operates with `8-DOF` (Degrees of Freedom), meaning each of its four legs has two pivot points
<br>

> [!TIP]
> Weight is your enemy. Because the MG90S servos are relatively weak, the chassis must be as lightweight as possible. Keep your design minimal!

### CAO
Now this is the part where you have to take your sketchs and make them in a CAD software. Iterate as many time until you are satisfied. *No need to print it yet.*<br>
<br>
My cad robot: <br>
<img width="428" height="364" alt="Screenshot_20260508_143424" src="https://github.com/user-attachments/assets/9bc27b7e-f8cc-4328-8bc1-0c3a4d382001" />

### Creating urdf file
#### What is an urdf file ?
It's simple! It's a file that describes your robot. This file will be used by your *simulation* software to make the robot move. Rather then having just a fixed 3d the urdf file specifies how parts move/rotate along side each other.
#### How to make it
You can:
- Either rebuild your robot in an urdf software like [D-Robotics](https://urdf.d-robotics.cc) or [Lever Robotics](https://lever-robotics.github.io/URDF_creator/). This can be done quick and dirty but can be less precise.<br>
- Or use your newly modeled robot to genereate it. [Here](https://docs.ros.org/en/humble/Tutorials/Intermediate/URDF/Exporting-an-URDF-File.html) is a tutorial for ROS on how to export your CAD file to an URDF file.

Don't forget to add your sensor to your urdf file!
> [!TIP]
> You will have to specifyl how each part move/rotates this can be tidius but you will have the exact replicate of your robot in the sim !

Speaking of [sim](https://github.com/joschmaCYU/quadruped#3---simulating-the-robot)
