#include <Arduino.h>
#include <Wire.h>
#include <micro_ros_arduino.h>
#include <stdio.h>
#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <std_msgs/msg/float64_multi_array.h>
#include <std_msgs/msg/float64.h>
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

// Gyroscope Publisher & Timer
rcl_publisher_t gyro_z_publisher;
std_msgs__msg__Float64 gyro_z_msg;
rcl_timer_t timer;

// --- IMU OBJECTS ---
Adafruit_BNO08x bno08x;
sh2_SensorValue_t sensorValue;

// --- STATE MANAGEMENT ---
enum states {
  WAITING_AGENT,
  AGENT_AVAILABLE,
  AGENT_CONNECTED,
  AGENT_DISCONNECTED
} state;

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

// --- GYRO PUBLISHER CALLBACK (Runs at 50Hz) ---
void timer_callback(rcl_timer_t * timer, int64_t last_call_time) {
  if (timer != NULL) {
    if (bno08x.getSensorEvent(&sensorValue)) {
      // Extraction de la vitesse angulaire réelle sur l'axe Z (Lacet / Yaw)
      if (sensorValue.sensorId == SH2_GYROSCOPE_CALIBRATED) {
        gyro_z_msg.data = sensorValue.un.gyroscope.z;
        rcl_publish(&gyro_z_publisher, &gyro_z_msg, NULL);
      }
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

// --- RECONNECTION LOGIC: CREATE ENTITIES ---
bool create_entities() {
  allocator = rcl_get_default_allocator();

  // Initialize micro-ROS support
  rcl_ret_t rc = rclc_support_init(&support, 0, NULL, &allocator);
  if (rc != RCL_RET_OK) return false;

  // Initialize Node
  rc = rclc_node_init_default(&node, "esp32_quadruped_node", "", &support);
  if (rc != RCL_RET_OK) return false;
  
  // Initialize Servo Subscriber
  rc = rclc_subscription_init_default(
    &subscriber,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Float64MultiArray),
    "/joint_group_position_controller/commands");
  if (rc != RCL_RET_OK) return false;

  // Initialize Gyro Publisher (Changement de type vers Float64)
  rc = rclc_publisher_init_default(
    &gyro_z_publisher,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Float64),
    "/gyro_z_speed");
  if (rc != RCL_RET_OK) return false;

  // Initialize Timer (50Hz -> 20ms)
  rc = rclc_timer_init_default(
    &timer,
    &support,
    RCL_MS_TO_NS(20),
    timer_callback);
  if (rc != RCL_RET_OK) return false;

  // Initialize Executor
  rc = rclc_executor_init(&executor, &support.context, 2, &allocator);
  if (rc != RCL_RET_OK) return false;
  
  rc = rclc_executor_add_subscription(&executor, &subscriber, &msg, &subscription_callback, ON_NEW_DATA);
  if (rc != RCL_RET_OK) return false;
  
  rc = rclc_executor_add_timer(&executor, &timer);
  if (rc != RCL_RET_OK) return false;

  return true;
}

// --- RECONNECTION LOGIC: DESTROY ENTITIES ---
void destroy_entities() {
  rcl_timer_fini(&timer);
  rclc_executor_fini(&executor);
  rcl_subscription_fini(&subscriber, &node);
  rcl_publisher_fini(&gyro_z_publisher, &node);
  rcl_node_fini(&node);
  rclc_support_fini(&support);
}

void setup() {
  pinMode(ledPin, OUTPUT);
  set_microros_transports();
  
  // 1. INITIALIZE I2C & IMU
  Wire.begin(21, 22);
  if (!bno08x.begin_I2C()) {
    error_loop(7); // Flash 7 times if IMU is unplugged or broken
  }
  
  // On demande uniquement le gyroscope calibré à 20000 microsecondes (50Hz)
  bno08x.enableReport(SH2_GYROSCOPE_CALIBRATED, 20000);

  // 2. INITIALIZE SERVOS
  for (int i = 0; i < 8; i++) {
    servos[i].setPeriodHertz(50);
    servos[i].attach(servoPins[i], 500, 2400); 
    servos[i].write(90); 
  }

  delay(2000);

  // 3. ALLOCATE MEMORY FOR SERVO ARRAY
  msg.data.capacity = 8;
  msg.data.data = (double*) malloc(msg.data.capacity * sizeof(double));
  msg.data.size = 0;

  state = WAITING_AGENT;
}

void loop() {
  switch (state) {
    case WAITING_AGENT:
      if (rmw_uros_ping_agent(100, 1) == RMW_RET_OK) {
        state = AGENT_AVAILABLE;
      } else {
        digitalWrite(ledPin, HIGH); delay(250);
        digitalWrite(ledPin, LOW); delay(250);
      }
      break;

    case AGENT_AVAILABLE:
      if (create_entities()) {
        state = AGENT_CONNECTED;
        digitalWrite(ledPin, HIGH); // Steady light on successful connection
      } else {
        state = WAITING_AGENT;
        destroy_entities();
      }
      break;

    case AGENT_CONNECTED:
      if (rclc_executor_spin_some(&executor, RCL_MS_TO_NS(10)) != RCL_RET_OK) {
        state = AGENT_DISCONNECTED;
      }
      break;

    case AGENT_DISCONNECTED:
      destroy_entities();
      state = WAITING_AGENT;
      break;

    default:
      break;
  }
}
