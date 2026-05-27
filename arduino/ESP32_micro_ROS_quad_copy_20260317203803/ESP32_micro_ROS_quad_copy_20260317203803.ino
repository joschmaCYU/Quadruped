#include <Arduino.h>
#include <Wire.h>
#include <micro_ros_arduino.h>
#include <stdio.h>
#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <std_msgs/msg/float64_multi_array.h>
#include <sensor_msgs/msg/imu.h>
#include <ESP32Servo.h>
#include <Adafruit_BNO08x.h>

// --- CONFIGURATION ---
const int servoPins[8] = {13, 14, 15, 16, 17, 18, 19, 23}; 
Servo servos[8];
const int ledPin = 2; 

// --- MICRO-ROS OBJECTS ---
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;
rclc_executor_t executor;

// Servo Subscriber
rcl_subscription_t subscriber;
std_msgs__msg__Float64MultiArray msg;

// IMU Publisher & Timer
rcl_publisher_t imu_publisher;
sensor_msgs__msg__Imu imu_msg;
rcl_timer_t timer;

// --- IMU OBJECTS ---
Adafruit_BNO08x bno08x;
sh2_SensorValue_t sensorValue;

// --- DIAGNOSTIC ERROR LOOP ---
void error_loop(int error_code){
  while(1){
    for(int i = 0; i < error_code; i++){
      digitalWrite(ledPin, HIGH); delay(250);
      digitalWrite(ledPin, LOW); delay(250);
    }
    delay(1500);
  }
}

// CRITICAL: MUST BE ON ONE LINE
#define RCCHECK(fn, code) { rcl_ret_t temp_rc = fn; if((temp_rc != RCL_RET_OK)){error_loop(code);}}

// --- IMU PUBLISHER CALLBACK (Runs at 50Hz) ---
void timer_callback(rcl_timer_t * timer, int64_t last_call_time) {
  if (timer != NULL) {
    if (bno08x.getSensorEvent(&sensorValue)) {
      
      // Update Quaternions (Absolute Orientation)
      if (sensorValue.sensorId == SH2_ROTATION_VECTOR) {
        imu_msg.orientation.x = sensorValue.un.rotationVector.i;
        imu_msg.orientation.y = sensorValue.un.rotationVector.j;
        imu_msg.orientation.z = sensorValue.un.rotationVector.k;
        imu_msg.orientation.w = sensorValue.un.rotationVector.real;
      }
      
      // Update Angular Velocity (Turn Speed in rad/s)
      if (sensorValue.sensorId == SH2_GYROSCOPE_CALIBRATED) {
        imu_msg.angular_velocity.x = sensorValue.un.gyroscope.x;
        imu_msg.angular_velocity.y = sensorValue.un.gyroscope.y;
        imu_msg.angular_velocity.z = sensorValue.un.gyroscope.z;
      }

      rcl_publish(&imu_publisher, &imu_msg, NULL);
    }
  }
}

// --- SERVO SUBSCRIBER CALLBACK ---
void subscription_callback(const void * msgin) {
  const std_msgs__msg__Float64MultiArray * incoming_msg = (const std_msgs__msg__Float64MultiArray *)msgin;
  
  digitalWrite(ledPin, !digitalRead(ledPin)); // Toggle LED on data received
  
  for (int i = 0; i < 8; i++) {
    float angle_rad = (float)incoming_msg->data.data[i];
    int angle_deg = (int)((angle_rad * 180.0) / PI) + 90;

    if (angle_deg < 0) angle_deg = 0;
    if (angle_deg > 180) angle_deg = 180;

    servos[i].write(angle_deg);
  }
}

void setup() {
  pinMode(ledPin, OUTPUT);
  set_microros_transports();
  
  // 1. INITIALIZE I2C & IMU
  Wire.begin(21, 22);
  if (!bno08x.begin_I2C()) {
    error_loop(7); // Flash 7 times if IMU is unplugged or broken
  }
  bno08x.enableReport(SH2_ROTATION_VECTOR, 20000); 
  bno08x.enableReport(SH2_GYROSCOPE_CALIBRATED, 20000);

  // 2. INITIALIZE SERVOS
  for (int i = 0; i < 8; i++) {
    servos[i].setPeriodHertz(50);
    servos[i].attach(servoPins[i], 500, 2400); 
    servos[i].write(90); 
  }

  delay(2000);
  allocator = rcl_get_default_allocator();

  // 3. ALLOCATE MEMORY FOR SERVO ARRAY
  msg.data.capacity = 8;
  msg.data.data = (double*) malloc(msg.data.capacity * sizeof(double));
  msg.data.size = 0;

  // 4. INIT MICRO-ROS CORE
  RCCHECK(rclc_support_init(&support, 0, NULL, &allocator), 1);
  RCCHECK(rclc_node_init_default(&node, "esp32_quadruped_node", "", &support), 2);
  
  // 5. INIT SUBSCRIBER (Reliable QoS for Motor Commands)
  RCCHECK(rclc_subscription_init_default(
    &subscriber,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Float64MultiArray),
    "/joint_group_position_controller/commands"), 3);

  // 6. INIT PUBLISHER (Best Effort QoS for High-Speed Sensor Data)
  RCCHECK(rclc_publisher_init_best_effort(
    &imu_publisher,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs, msg, Imu),
    "/imu"), 4);

  // 7. INIT TIMER (Runs the IMU Publisher at 50Hz / 20ms)
  RCCHECK(rclc_timer_init_default(
    &timer,
    &support,
    RCL_MS_TO_NS(20),
    timer_callback), 5);
    
  // Assign static frame_id for IMU to link it to the TF tree
  imu_msg.header.frame_id.data = (char*)"imu_link";
  imu_msg.header.frame_id.size = strlen(imu_msg.header.frame_id.data);
  imu_msg.header.frame_id.capacity = imu_msg.header.frame_id.size + 1;

  // 8. INIT EXECUTOR (Capacity set to 2: One for Subscriber, One for Timer)
  RCCHECK(rclc_executor_init(&executor, &support.context, 2, &allocator), 6);
  RCCHECK(rclc_executor_add_subscription(&executor, &subscriber, &msg, &subscription_callback, ON_NEW_DATA), 7);
  RCCHECK(rclc_executor_add_timer(&executor, &timer), 8);
}

void loop() {
  RCCHECK(rclc_executor_spin_some(&executor, RCL_MS_TO_NS(10)), 9);
}
