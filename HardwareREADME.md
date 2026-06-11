### HardwareREADME.md

# Building the Physical Robot

Time to put the hardware together! Moving from simulation to a physical quadruped requires strict attention to power distribution and data bus management.

## Critical Assembly Rules

* **Power Isolation:** Servos draw massive spikes of current when lifting the robot. Power your Raspberry Pi from one UBEC, and your 8 servos from a second 6A UBEC. Never try to pull servo power through the Pi or the ESP32.
* **Common Ground:** This is the most frequent hardware bug. You MUST tie the ground wire of your ESP32 to the ground wire of your Servo UBEC. If you don't, the PWM signals will float and your servos will twitch violently.
* **The I2C Bus:** Connect your BNO085 IMU to the ESP32 using pins 21 (SDA) and 22 (SCL). Reserve these communication lanes exclusively for the sensor.
* **LiDAR Data:** Plug the LD19 LiDAR directly into one of the Raspberry Pi's USB ports (usually mounting as `/dev/ttyUSB1`).

---

## Roadblocks & Solutions: Hardware Quirks

Physics doesn't care about your code. Here is the main electrical hurdle I had to overcome during the build.

### The 4.43V Servo Brownout
**The Problem:** Despite using a 5V/6V 3A adjustable UBEC to power the servos, a multimeter showed the output maxing out at exactly 4.43V. The servos lacked the torque to lift the robot's body.
**The Fix:** A UBEC is a step-down (buck) converter, not a voltage multiplier. It has a physical "dropout voltage" of around 0.6V and requires an input voltage strictly higher than its target output. Feeding 5V from a basic power supply into a UBEC to get 5V out mathematically results in a drop to ~4.4V. 
I solved this by supplying the UBEC directly from a **7.4V (2S)** LiPo battery. The output
