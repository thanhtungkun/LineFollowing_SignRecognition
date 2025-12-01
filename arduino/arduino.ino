#define TCRT5000_LEFT A0
#define TCRT5000_CENTER_LEFT A1
#define TCRT5000_CENTER_RIGHT A2
#define TCRT5000_RIGHT A3
#define IN1 7
#define IN2 6
#define IN3 5
#define IN4 4
#define ENA 11
#define ENB 10
#define MAX_SPEED 255  //từ 0-255
#define MIN_SPEED 0
String navigation_sign = "NULL";
bool setup_sent = false;
int sign_stop = 0;

void setup() {
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(TCRT5000_LEFT, INPUT);
  pinMode(TCRT5000_CENTER_LEFT, INPUT);
  pinMode(TCRT5000_RIGHT, INPUT);
  pinMode(TCRT5000_CENTER_RIGHT, INPUT);
  Serial.begin(9600);
  setup_sent = false;
}

void motor_Dung() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}

void motor_Tien(int level) {  // Cả 2 motor tiến cùng chiều

  int speed = MAX_SPEED - constrain(level, MIN_SPEED, MAX_SPEED);

  digitalWrite(IN1, HIGH);
  digitalWrite(IN4, HIGH);

  analogWrite(IN2, speed);
  analogWrite(IN3, speed);
}

void motor_Phai(int level, int max, int min) {
  int speed = MAX_SPEED - constrain(level, MIN_SPEED, MAX_SPEED);
  digitalWrite(IN1, HIGH);
  analogWrite(IN2, speed);
  analogWrite(IN3, speed * 0.7);
  digitalWrite(IN4, LOW);
}

void motor_Trai(int level, int max, int min) {
  int speed = MAX_SPEED - constrain(level, MIN_SPEED, MAX_SPEED);

  digitalWrite(IN1, LOW);
  analogWrite(IN2, speed * 0.7);
  analogWrite(IN3, speed);
  digitalWrite(IN4, HIGH);
}

void motor_Lui(int level) {  // Cả 2 motor lùi cùng chiều

  int speed = MAX_SPEED - constrain(level, MIN_SPEED, MAX_SPEED);
  digitalWrite(IN1, LOW);
  analogWrite(IN2, speed);
  analogWrite(IN3, speed);
  digitalWrite(IN4, LOW);
}


void controlNavigation() {
  int analog_left = digitalRead(TCRT5000_LEFT);
  int analog_right = digitalRead(TCRT5000_RIGHT);
  int analog_center_left = digitalRead(TCRT5000_CENTER_LEFT);
  int analog_center_right = digitalRead(TCRT5000_CENTER_RIGHT);

  unsigned long startTime = millis();

  if (analog_left == 1 && navigation_sign.equals("left")) {
    delay(350);
    while (millis() - startTime < 550) {  // Giữ trạng thái rẽ trong 4 giây
      motor_Trai(100, 200, 0);
    }
    navigation_sign = "straight";
  } else if (analog_right == 1 && navigation_sign.equals("right")) {
    delay(350);
    while (millis() - startTime < 550) {  // Giữ trạng thái rẽ trong 4 giây
      motor_Phai(100, 200, 0);
    }
    navigation_sign = "straight";
  } else if (analog_center_right == 1 && analog_center_left == 0) {
    motor_Phai(100, 200, 0);
    delay(30);
    //Move Right
  } else if (analog_center_right == 0 && analog_center_left == 1) {
    motor_Trai(100, 200, 0);  //Move Left
    delay(30);
  } else if (analog_center_right == 1 && analog_center_left == 1) {
    if (navigation_sign.equals("straight")) {
      setup_sent = false;
    }
    if (navigation_sign.equals("stop") && sign_stop < 15) {
      sign_stop = 0;
      motor_Dung();
    } else motor_Tien(40);
  } else if (navigation_sign.equals("stop")) {
    sign_stop = 0;
    motor_Dung();
  }
  sign_stop++;
}
int timeout = 0;
void loop() {

  controlNavigation();

  if (!setup_sent) {
    Serial.println("setUp");  // Gửi lệnh setup đến Raspberry
    setup_sent = true;        // Đánh dấu đã gửi
  }

  if (Serial.available()) {
    String received = Serial.readStringUntil('\n');
    navigation_sign = received;
  }

}
