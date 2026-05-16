#include <ESP32Servo.h>

#define SERVO_A_PIN 4
#define SERVO_B_PIN 5
#define SERVO_C_PIN 6
#define SERVO_D_PIN 7

Servo servoA, servoB, servoC, servoD;

void setup() {
  Serial0.begin(115200);
  delay(2000);

  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  servoA.attach(SERVO_A_PIN, 500, 2400);
  servoB.attach(SERVO_B_PIN, 500, 2400);
  servoC.attach(SERVO_C_PIN, 500, 2400);
  servoD.attach(SERVO_D_PIN, 500, 2400);

  servoA.write(90);
  servoB.write(90);
  servoC.write(90);
  servoD.write(90);

  Serial0.println("READY");
}

void loop() {
  if (Serial0.available()) {
    String line = Serial0.readStringUntil('\n');
    line.trim();
    int s1, s2, s3, s4;
    if (sscanf(line.c_str(), "S1:%d,S2:%d,S3:%d,S4:%d", &s1, &s2, &s3, &s4) == 4) {
      servoA.write(s1);
      servoB.write(s2);
      servoC.write(s3);
      servoD.write(s4);
      Serial0.println("OK");
    } else {
      Serial0.print("ERR:");
      Serial0.println(line);
    }
  }
}