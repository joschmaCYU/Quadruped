#include <ESP32Servo.h>

Servo myServo;
int servoPin = 13;

void setup() {
  // The ESP32 requires hardware timers to be allocated for PWM signals
  ESP32PWM::allocateTimer(0);
  
  // Standard servos operate at 50Hz
  myServo.setPeriodHertz(50);    
  
  // Attach the servo to pin 13
  myServo.attach(servoPin, 500, 2400); 
}

void loop() {
  // Sweep from 0 to 180 degrees
  for (int pos = 0; pos <= 180; pos += 1) { 
    myServo.write(pos);    
    delay(15); // Wait 15ms for the gears to physically move          
  }
  
  // Sweep from 180 back to 0 degrees
  for (int pos = 180; pos >= 0; pos -= 1) { 
    myServo.write(pos);    
    delay(15);             
  }
}