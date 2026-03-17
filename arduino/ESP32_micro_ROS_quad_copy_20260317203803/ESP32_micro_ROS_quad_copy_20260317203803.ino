#include <Arduino.h>
#include <micro_ros_arduino.h>
#include <stdio.h>
#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <sensor_msgs/msg/joint_state.h>
#include <ESP32Servo.h>

// --- CONFIGURATION ---
const int servoPins[8] = {13, 14, 15, 16, 17, 18, 19, 21}; 
Servo servos[8];
const int ledPin = 2; 

// --- MICRO-ROS OBJECTS ---
rcl_subscription_t subscriber;
sensor_msgs__msg__JointState msg;
rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;

// MEMORY BUFFERS FOR THE HEAVY JOINTSTATE MESSAGE
double msg_position_data[8];
rosidl_runtime_c__String msg_name_data[8];
char name_buffers[8][50]; 

// --- DIAGNOSTIC ERROR LOOP ---
void error_loop(int error_code){
  while(1){
    // It will blink the LED 'error_code' times, pause, and repeat
    for(int i = 0; i < error_code; i++){
      digitalWrite(ledPin, HIGH); delay(250);
      digitalWrite(ledPin, LOW); delay(250);
    }
    delay(1500);
  }
}

#define RCCHECK(fn, code) { rcl_ret_t temp_rc = fn; if((temp_rc != RCL_RET_OK)){error_loop(code);}}

// --- CALLBACK ---
void subscription_callback(const void * msgin) {
  const sensor_msgs__msg__JointState * incoming_msg = (const sensor_msgs__msg__JointState *)msgin;
  
  // Flash LED rapidly on receive
  digitalWrite(ledPin, !digitalRead(ledPin)); 
  
  if (incoming_msg->position.size >= 8) {
    for (int i = 0; i < 8; i++) {
      float angle_rad = incoming_msg->position.data[i];
      int angle_deg = (int)((angle_rad * 180.0) / PI) + 90;

      if (angle_deg < 0) angle_deg = 0;
      if (angle_deg > 180) angle_deg = 180;

      servos[i].write(angle_deg);
    }
  }
}

void setup() {
  pinMode(ledPin, OUTPUT);
  set_microros_transports();
  
  for (int i = 0; i < 8; i++) {
    servos[i].setPeriodHertz(50);
    servos[i].attach(servoPins[i], 500, 2400); 
    servos[i].write(90); 
  }

  delay(2000);
  allocator = rcl_get_default_allocator();

  // --- MEMORY ALLOCATION (THE CRITICAL FIX) ---
  msg.name.capacity = 8;
  msg.name.data = msg_name_data;
  for(int i = 0; i < 8; i++){
      msg.name.data[i].capacity = 50;
      msg.name.data[i].data = name_buffers[i];
      msg.name.data[i].size = 0;
  }
  
  msg.position.capacity = 8;
  msg.position.data = msg_position_data;
  msg.position.size = 0;

  // EXPLICITLY ZERO OUT UNUSED ARRAYS TO PREVENT SEGFAULTS!
  msg.velocity.capacity = 0;
  msg.velocity.size = 0;
  msg.velocity.data = NULL;
  
  msg.effort.capacity = 0;
  msg.effort.size = 0;
  msg.effort.data = NULL;

  // --- INITIALIZATION WITH ERROR CODES ---
  // If it fails here, it will blink exactly this many times
  RCCHECK(rclc_support_init(&support, 0, NULL, &allocator), 1);
  RCCHECK(rclc_node_init_default(&node, "esp32_servo_node", "", &support), 2);
  RCCHECK(rclc_subscription_init_default(
    &subscriber,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs, msg, JointState),
    "joint_states"), 3);
  RCCHECK(rclc_executor_init(&executor, &support.context, 1, &allocator), 4);
  
  RCCHECK(rclc_executor_add_subscription(&executor, &subscriber, &msg, &subscription_callback, ON_NEW_DATA), 5);
}

void loop() {
  // If executor fails during spin, blink 6 times
  RCCHECK(rclc_executor_spin_some(&executor, RCL_MS_TO_NS(10)), 6);
}