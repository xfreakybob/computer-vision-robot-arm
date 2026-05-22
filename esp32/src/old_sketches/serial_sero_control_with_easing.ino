#include <ServoEasing.hpp>

#define SERVO_A_PIN 4
#define SERVO_B_PIN 5
#define SERVO_C_PIN 6
#define SERVO_D_PIN 7

ServoEasing servoA, servoB, servoC, servoD;

void setup() {
  Serial0.begin(115200);
  delay(2000);

  // Attach servos and set initial position to 90 degrees
  servoA.attach(SERVO_A_PIN, 90, 500, 2400);
  servoB.attach(SERVO_B_PIN, 90, 500, 2400);
  servoC.attach(SERVO_C_PIN, 90, 500, 2400);
  servoD.attach(SERVO_D_PIN, 90, 500, 2400);

  // Set speed in degrees per second
  servoA.setSpeed(90);
  servoB.setSpeed(30);  // shoulder slower (resonance-prone)
  servoC.setSpeed(60);
  servoD.setSpeed(90);

  // Set easing type — IN_OUT variants ramp up and down smoothly
  servoA.setEasingType(EASE_CUBIC_IN_OUT);
  servoB.setEasingType(EASE_QUARTIC_IN_OUT);  // gentlest for shoulder
  servoC.setEasingType(EASE_CUBIC_IN_OUT);
  servoD.setEasingType(EASE_CUBIC_IN_OUT);

  Serial0.println("READY");
}

void loop() {
  if (Serial0.available()) {
    String line = Serial0.readStringUntil('\n');
    line.trim();
    int s1, s2, s3, s4;
    if (sscanf(line.c_str(), "S1:%d,S2:%d,S3:%d,S4:%d", &s1, &s2, &s3, &s4) == 4) {
      servoA.startEaseTo(s1);
      servoB.startEaseTo(s2);
      servoC.startEaseTo(s3);
      servoD.startEaseTo(s4);
      Serial0.println("OK");
    } else {
      Serial0.print("ERR:");
      Serial0.println(line);
    }
  }
}