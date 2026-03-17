#include <micro_ros_arduino.h>
#include <stdio.h>
#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <std_msgs/msg/int32.h>
#include <rmw_microros/rmw_microros.h>
#include <ESP32Servo.h>

#define LED_PIN 2
#define SERVO_PIN 13

// Error handling macros
#define RCCHECK(fn, code) { rcl_ret_t temp_rc = fn; if((temp_rc != RCL_RET_OK)){ error_loop(code); }}
#define RCSOFTCHECK(fn) { rcl_ret_t temp_rc = fn; if((temp_rc != RCL_RET_OK)){}}

rcl_subscription_t subscriber;
std_msgs__msg__Int32 sub_msg;
rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;

Servo myServo;

void error_loop(int error_code) {
  while(1) {
    for(int i = 0; i < error_code; i++) {
      digitalWrite(LED_PIN, HIGH); delay(250);
      digitalWrite(LED_PIN, LOW); delay(250);
    }
    delay(1500);
  }
}

// Fires instantly when the Python script publishes an angle
void subscription_callback(const void * msgin) {
  const std_msgs__msg__Int32 * msg = (const std_msgs__msg__Int32 *)msgin;
  int target_angle = msg->data;
  
  // Constrain limits to protect the physical gears
  if (target_angle >= 0 && target_angle <= 180) {
    myServo.write(target_angle);
  }
}

void setup() {
  set_microros_transports(); 
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW); 

  // Initialize the Servo
  ESP32PWM::allocateTimer(0);
  myServo.setPeriodHertz(50);
  myServo.attach(SERVO_PIN, 500, 2400);
  myServo.write(90); // Start centered
  
  delay(2000);
  allocator = rcl_get_default_allocator();

  // Wait for the Agent to connect (Flash LED while searching)
  while (rmw_uros_ping_agent(1000, 1) != RCL_RET_OK) {
    digitalWrite(LED_PIN, HIGH); delay(100);
    digitalWrite(LED_PIN, LOW); delay(400);
  }
  digitalWrite(LED_PIN, HIGH);

  // Init Node and Subscriber (Using the safe "my_robot" namespace)
  RCCHECK(rclc_support_init(&support, 0, NULL, &allocator), 1);
  RCCHECK(rclc_node_init_default(&node, "esp_servo_listener", "my_robot", &support), 2);
  RCCHECK(rclc_subscription_init_default(&subscriber, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32), "servo_cmd"), 3);

  // Init Executor
  RCCHECK(rclc_executor_init(&executor, &support.context, 1, &allocator), 4);
  RCCHECK(rclc_executor_add_subscription(&executor, &subscriber, &sub_msg, &subscription_callback, ON_NEW_DATA), 5);

  digitalWrite(LED_PIN, LOW); // Turn LED off to indicate readiness
}

void loop() {
  delay(10);
  rclc_executor_spin_some(&executor, RCL_MS_TO_NS(10));
}