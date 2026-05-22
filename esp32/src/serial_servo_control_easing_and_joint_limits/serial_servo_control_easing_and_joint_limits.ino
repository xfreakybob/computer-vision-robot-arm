#include <ServoEasing.hpp>

#define SERVO_A_PIN 4
#define SERVO_B_PIN 5
#define SERVO_C_PIN 6
#define SERVO_D_PIN 7

ServoEasing servoA, servoB, servoC, servoD;

// Per-joint safe operating limits (5° margin inside measured absolute limits)
// Absolute limits from Week 2 testing: A: 0-190, B: 0-160, C: 0-190, D: 15-120
struct JointLimits {
  int min_angle;
  int max_angle;
};

const JointLimits LIMITS[4] = {
  {5, 185},   // Servo A (base)
  {5, 155},   // Servo B (shoulder)
  {5, 185},   // Servo C (elbow)
  {20, 115}   // Servo D (gripper)
};

void setup() {
  Serial0.begin(115200);
  delay(2000);

  servoA.attach(SERVO_A_PIN, 90, 500, 2400);
  servoB.attach(SERVO_B_PIN, 90, 500, 2400);
  servoC.attach(SERVO_C_PIN, 90, 500, 2400);
  servoD.attach(SERVO_D_PIN, 90, 500, 2400);

  servoA.setSpeed(90);
  servoB.setSpeed(30);
  servoC.setSpeed(60);
  servoD.setSpeed(90);

  servoA.setEasingType(EASE_CUBIC_IN_OUT);
  servoB.setEasingType(EASE_QUARTIC_IN_OUT);
  servoC.setEasingType(EASE_CUBIC_IN_OUT);
  servoD.setEasingType(EASE_CUBIC_IN_OUT);

  Serial0.println("READY");
}

// Returns true if all angles are within bounds.
// On failure, sets failed_joint to 1-4 indicating which joint was out of range.
bool validateAngles(int s1, int s2, int s3, int s4, int &failed_joint) {
  int angles[4] = {s1, s2, s3, s4};
  for (int i = 0; i < 4; i++) {
    if (angles[i] < LIMITS[i].min_angle || angles[i] > LIMITS[i].max_angle) {
      failed_joint = i + 1;
      return false;
    }
  }
  return true;
}

void loop() {
  if (Serial0.available()) {
    String line = Serial0.readStringUntil('\n');
    line.trim();
    int s1, s2, s3, s4;
    if (sscanf(line.c_str(), "S1:%d,S2:%d,S3:%d,S4:%d", &s1, &s2, &s3, &s4) == 4) {
      int failed_joint = 0;
      if (!validateAngles(s1, s2, s3, s4, failed_joint)) {
        Serial0.print("ERR:OUT_OF_RANGE,joint=S");
        Serial0.print(failed_joint);
        Serial0.print(",min=");
        Serial0.print(LIMITS[failed_joint - 1].min_angle);
        Serial0.print(",max=");
        Serial0.println(LIMITS[failed_joint - 1].max_angle);
      } else {
        servoA.startEaseTo(s1);
        servoB.startEaseTo(s2);
        servoC.startEaseTo(s3);
        servoD.startEaseTo(s4);
        Serial0.println("OK");
      }
    } else {
      Serial0.print("ERR:PARSE_FAIL,");
      Serial0.println(line);
    }
  }
}