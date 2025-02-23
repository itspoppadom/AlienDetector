#include <Servo.h>
#include <NewPing.h>

#define TRIGGER_PIN_1 12
#define ECHO_PIN_1 11

#define TRIGGER_PIN_2 9
#define ECHO_PIN_2 8

#define MAX_DISTANCE 150

Servo myservo1;
Servo myservo2;

NewPing sonar1(TRIGGER_PIN_1, ECHO_PIN_1, MAX_DISTANCE);
NewPing sonar2(TRIGGER_PIN_2, ECHO_PIN_2, MAX_DISTANCE);

uint8_t distance1;
uint8_t distance2;

uint8_t degre1 = 0;
uint8_t degre2 = 0;

uint8_t degre_step = 15;

bool increasing1 = true;
bool increasing2 = true;

void setup() {
  Serial.begin(115200);
  myservo1.attach(10);
  myservo1.write(90);
  delay(300);
  myservo2.attach(7);
  myservo2.write(0);
  delay(300);
}

void loop() {
  // Set servos to current angles
  myservo1.write(degre1);
  delay(200);
  myservo2.write(degre2);
  delay(200);  // give the servos time to reach the position

  // Read distances (in centimeters) from the ultrasonic sensors
  distance1 = sonar1.ping_cm();
  delay(50);
  distance2 = sonar2.ping_cm();
  delay(50);

  // Create JSON if at least one sensor has detected an object
  int amount = 0;
  String json = "{";
  String arr = "";

  // For servo1
  if (distance1 > 0 && distance1 <= MAX_DISTANCE) {
    arr += "{\"degree\": " + String(map(degre2, 0, 90, 90, 0)) + ", \"distance\": " + String(distance1) + "}";
    amount++;
  }

  // For servo2
  if (distance2 > 0 && distance2 <= MAX_DISTANCE) {
    if (arr.length() > 0) {
      arr += ", ";
    }
    arr += "{\"degree\": " + String(degre2 + 90) + ", \"distance\": " + String(distance2) + "}";
    amount++;
  }

  json += "\"amount\": " + String(amount) + ", \"arr\": [" + arr + "]}";

  // Only send JSON if at least one sensor detected something
  if (amount > 0) {
    Serial.println(json);
  }

  // Update servo1 angle
  if (increasing1) {
    if (degre1 >= 90) {
      increasing1 = false;
      degre1 -= degre_step;
    } else {
      degre1 += degre_step;
    }
  } else {
    if (degre1 <= 0) {
      increasing1 = true;
      degre1 += degre_step;
    } else {
      degre1 -= degre_step;
    }
  }

  // Update servo2 angle
  if (increasing2) {
    if (degre2 >= 90) {
      increasing2 = false;
      degre2 -= degre_step;
    } else {
      degre2 += degre_step;
    }
  } else {
    if (degre2 <= 0) {
      increasing2 = true;
      degre2 += degre_step;
    } else {
      degre2 -= degre_step;
    }
  }

  // delay(300);
}
