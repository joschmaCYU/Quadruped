## 1 - Parts
For our robot to exist it needs a body. We will cover the three main pillars of our build: computation, perception, and power management. 

<img width="844" height="466" src="https://github.com/user-attachments/assets/6417944d-0f2c-459d-984a-4ef052d83b80" />

### Computation
As stated before we will be using ROS 2 but it needs something powerfull to run ! But we also need some thing to communicate with the servos and other actuators.
- The brain: `raspberry pi`
- The musclues: `ESP32`

You could plug everything but the rasp has only 4 PWM pins and you can't just plug the servos to any GPIO pins else they will not act as you want.<br>

### Perception
To sens the world I choose a `2D lidar`. This will mesure how far away the obstacles are. I choose a ld-19 but any lidar will do the trick. <br>
To sens how our robot will move we will need an `IMU`.

> [!TIP]
> You don't need to place the lidar low to the ground because you will be able to move your legs up, so even if the lidar doesn't detect the obstacle your robot will still be able to pass over it.

### Power
The power side isn't more complicated. If you want to move multiple servos at the same time your boards will not provide sufficiant power you will need a battery.<br>
I chose a small `2200mAh (3S) LiPo battery`. This battery has 3 cells that will produce 11.1V.<br>
But the servos need 5v to operate, so you need to make sure to provide exaclty these 5v else your servo will... hmmmm... not function very well. So you will need a `5V/6A UBEC` which regulates the voltage. Why 6A ? Because each mg90s uses a max of 750mA * 8 = 6000mA at 5V.

> [!WARNING]
> You should always use a more powerfull device to not burn it.  
> If your servo use more then 6A be sure to take a more powerfull UBEC.  
> You also should be carfull between peek and sustain consumption.  
<br>

### The motors
For the motors I went with simple dirt cheap (and weak) MG-90S. Why ? Hmmmm... I may or may not have more have more then 200 of them lying around. Yeaaaaa don't ask to many question. But jokes a part in robotics we often reuse old parts that we have lying around and it isn't a bad idea!

Do not forget the rasperry pi which needs also 5V but will not pull more then 3A so I took a `5V/3A UBEC` for it!

<details>
<summary>Sketch of my electronic:</summary>

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
        LD19("LiDAR<br>(via CP2102 USB board)"):::sensor
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

</details>

> [!TIP]
> You can add some other sensors like: foot contact sensors, a depth camera, ToF sensors, power monitoring

With all of that in mind we can begging with [printing](https://github.com/joschmaCYU/quadruped#2---print--assemble)
