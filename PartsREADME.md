### 1 - Parts
As stated before we will be using ROS 2 but it needs power to run ! Thats why you will need something powerfull like a raspberry pi 5. To communicate with the servos and other actuators I choose an ESP32. You could plug everything but the rasp has only 4 PWM pins and you can't just plug the servos to any GPIO pins else they will not act as you want.<br>
To sens the world I choose a 2D lidar (for SLAM/Navigation). This will mesure how far away the obstacles are.

> [!TIP]
> You don't need to place the lidar low to the ground because you will be able to move your legs up, so even if the lidar doesn't detect the obstacle your robot will still be able to pass over it.

The power side is much more strait forward. If you want to move multiple servos at the same time your boards will not provide sufficiant power you will need a battery. I choose a small 2200mAh LiPo Battery. The servos need 5v to operate you need to make sure to provide these 5v to much and your servo will burn and to little they will not move. So you will need a 5V/6A UBEC which regulates the voltage and has a max current of 6A
> [!WARNING]
> If your servo use more then 6A be sure to take a more powerfull UBEC


And the rasp needs also 5V but will not pull more then 3A so I took a 5V/3A UBEC for it!

Sketch of my electronic:
```mermaid
graph TD
    %% Define Styles
    classDef power fill:#c0392b,stroke:#e74c3c,stroke-width:2px,color:#fff
    classDef compute fill:#2c3e50,stroke:#34495e,stroke-width:2px,color:#ecf0f1
    classDef sensor fill:#8e44ad,stroke:#9b59b6,stroke-width:2px,color:#fff
    classDef motor fill:#e67e22,stroke:#d35400,stroke-width:2px,color:#fff

    subgraph Power_Distribution ["Power Sources & Regulators"]
        BATT("LiPo Battery<br>(3S 11.1V)"):::power
        UBEC_ESP("Brain UBEC<br>(5V 3A)"):::power
        UBEC_SRV("Motor UBEC<br>(5V 6A)"):::power
    end

    subgraph Computing ["Logic & Processing"]
        PC("Main PC / Raspberry Pi"):::compute
        ESP32("ESP32 (VIN Pin)"):::compute
    end

    subgraph Peripherals ["Sensors & Actuators"]
        SERVOS("8x Servos<br>(V+, GND, Signal)"):::motor
        IMU("BNO085 IMU"):::sensor
        LD19("LD19 LiDAR<br>(via CP2102 USB board)"):::sensor
    end

    %% --- POWER ROUTING (Solid Lines) ---
    BATT -->|"Raw Battery Voltage (+)"| UBEC_ESP
    BATT -->|"Raw Battery Voltage (+)"| UBEC_SRV

    UBEC_ESP -->|"5V (+)"| PC
    UBEC_SRV -->|"Servo Voltage (5V)"| SERVOS

    ESP32 -->|"3.3V Out (+)"| IMU
    PC -->|"USB 5V (+)"| LD19

    %% --- GROUND ROUTING (Dotted Lines) ---
    BATT -.->|"GND (-)"| UBEC_ESP
    BATT -.->|"GND (-)"| UBEC_SRV
    UBEC_ESP -.->|"GND"| PC
    UBEC_SRV -.->|"GND"| SERVOS
    ESP32 -.->|"GND"| IMU

    %% CRITICAL: Common Ground Tie
    ESP32 -.->|"CRITICAL: Common GND Tie"| UBEC_SRV

    %% --- DATA ROUTING (Thick Lines) ---
    PC -->|"USB 5V (+)"| ESP32
    PC ===|"USB Data (ttyUSB0)"| ESP32
    PC ===|"USB Data (ttyUSB1)"| LD19

    ESP32 ===|"I2C SDA (e.g., GPIO 21)"| IMU
    ESP32 ===|"I2C SCL (e.g., GPIO 22)"| IMU

    ESP32 ===|"8x PWM Signal Wires"| SERVOS
```


> [!TIP]
> You can add some other sensors like: foot contact sensors, a depth camera, ToF sensors, power monitoring

With all of that in mind we can begging with [printing](https://github.com/joschmaCYU/quadruped#2---print--assemble)
