#include <Arduino.h>

// Pin assignments
#define STEP_PIN           4
#define DIR_PIN            3
#define MS0                7
#define MS1                6
#define MS2                5
#define DEW_HEATER_PIN     2
#define STEP_EN_PIN        8
#define LIM_PIN            9
#define BUTTON_PIN         A0

// Button definitions
#define BUTTON_TOLERANCE   20
#define BUTTON_DOWN        418
#define BUTTON_UP          719
#define BUTTON_STEP_SIZE   100
#define BUTTON_DEBOUNCE_MS 50

// Direction definitions
#define DIR_OUT            HIGH
#define DIR_IN             LOW
#define HOMING_DIR         DIR_IN
// Homing pos delta.
// Basically, how far the motor should move after homing to reach zero.
#define HOMING_REF_POS 0

// The period of dew heater oscillations.
#define DEW_HEATER_PERIOD_MS 10000
#define ACTIVE_DEW_HEATER_STATE 1

// Voltage measurement definitions
#define VOLTAGE_MEASURE_PIN A7
// MEASURED values of the dividers to measure voltage.
#define VOLTAGE_DIV_R1 10000
#define VOLTAGE_DIV_R2 5000
#define VOLTAGE_SUPPLY 5.0

// Serial Definitions
#define SERIAL_SPEED 9600
#define COMM_SERIAL Serial

// Command Definitions
#define DFL_MOVE_COMMAND    "DFL:MOVE"
#define DFL_GET_COMMAND     "DFL:GET"
#define DFL_HOME_COMMAND    "DFL:HOME"
#define DFL_ABORT_COMMAND   "DFL:ABORT"
#define DFL_HEATER_COMMAND  "DFL:HEATER"
#define DFL_VOLTAGE_COMMAND "DFL:VOLTAGE"

// Steps per second
#define HOMING_SPEED 200
#define MOVING_SPEED 500
#define IDLE_SPEED 0
#define ENABLED_WHEN_IDLE false

enum StepMode {
  HOMING,
  MOVING,
  IDLE
};

int32_t  step_index             = 0;
int32_t  target                 = 0;
uint32_t last_step_time         = 0;
bool     last_step_pin_state    = false;
uint8_t  heater_power           = 0;
bool     last_up_button_state   = false;
uint32_t last_up_button_time    = 0;
bool     last_down_button_state = false;
uint32_t last_down_button_time  = 0;
uint8_t  direction              = DIR_IN;

// Function prototypes
void     handle_step();
void     handle_buttons();
void     handle_input();
void     handle_heater();
uint32_t get_move_interval(StepMode);
void     set_mode(StepMode);
float    measure_voltage();
void     print_mode();

enum StepMode stepMode = HOMING;

uint32_t get_move_interval(StepMode mode) {
  switch(mode) {
    case HOMING:
      return 1000000 / HOMING_SPEED;
    case MOVING:
      return 1000000 / MOVING_SPEED;
    default:
      return 0; // Raise an error?
  }
}

void setup() {
  COMM_SERIAL.begin(SERIAL_SPEED);
  // Do nothing until serial is connected.
  while(!COMM_SERIAL);
  COMM_SERIAL.println("DFL: Beginning initialisation...");

  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(STEP_EN_PIN, OUTPUT);
  pinMode(VOLTAGE_MEASURE_PIN, INPUT);
  pinMode(LIM_PIN, INPUT_PULLUP);
  pinMode(MS0, OUTPUT);
  pinMode(MS1, OUTPUT);
  pinMode(MS2, OUTPUT);
  pinMode(DEW_HEATER_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(LIM_PIN, INPUT_PULLUP);

  digitalWrite(STEP_EN_PIN, LOW);
  digitalWrite(MS0, LOW);
  digitalWrite(MS1, LOW);
  digitalWrite(MS2, LOW);
 
  set_mode(HOMING);
  COMM_SERIAL.println("DFL: Started homing...");
}


void loop() {
  handle_step();
  handle_input();
  handle_buttons();
  handle_heater();
}

void set_target(int32_t new_target) {
  if(new_target > target) {
    direction = DIR_OUT;
  } else if(new_target < target) {
    direction = DIR_IN;
  }
  target = new_target;
}

void print_mode() {
  set_mode(stepMode);
}

void set_mode(StepMode mode) {
  stepMode = mode;
  digitalWrite(STEP_EN_PIN, !(mode != IDLE || ENABLED_WHEN_IDLE));
  switch(stepMode) {
    case MOVING:
      COMM_SERIAL.println("DFL: MOVING");
      return;
    case HOMING:
      COMM_SERIAL.println("DFL: HOMING");
      return;
    case IDLE:
      COMM_SERIAL.println("DFL: IDLE");
      return;
    default:
      COMM_SERIAL.println("DFL: Entered unknown state.");
      return;
  }
}

void handle_input() {
  if(COMM_SERIAL.available() > 0) {
    // Does this work?
    String input = COMM_SERIAL.readStringUntil(' ');
    input.trim();
   
    if(input == DFL_MOVE_COMMAND) {
      String input = COMM_SERIAL.readStringUntil('\n');
      if(input.length() == 0) {
        COMM_SERIAL.println("DFL: No position provided.");
        return;
      }
      uint32_t move_pos = input.toInt();
      if(move_pos == 0) {
        COMM_SERIAL.println("DFL: Could not parse position, or provided 0.");
        return;
      }
      // Sanity check move position.
      if(move_pos == step_index) {
        COMM_SERIAL.println("DFL: Already at that position.");
        return;
      }
      //Set target position, and change to moving mode.
      set_target(move_pos + target);
      COMM_SERIAL.println("DFL: Set target to position " + (String)target);
      set_mode(MOVING);
    } else if (input == DFL_HOME_COMMAND) {
      // Home DFL
      // Clear the rest of the serial buffer since we don't need to read it.
      COMM_SERIAL.readStringUntil('\n');
      COMM_SERIAL.println("DFL: Started homing.");
      set_mode(HOMING);
    } else if (input == DFL_ABORT_COMMAND) {
      COMM_SERIAL.readStringUntil('\n');
      COMM_SERIAL.println("DFL: Aborted movement.");
      set_mode(IDLE);
      target = step_index;
    } else if (input == DFL_GET_COMMAND) {
      COMM_SERIAL.readStringUntil('\n');
      COMM_SERIAL.println("DFL: " + (String)step_index + " (Target: " + (String)target + ")");
      print_mode();
    } else if (input == DFL_HEATER_COMMAND) {
      String input = COMM_SERIAL.readStringUntil('\n');
      if (input.length() == 0) {
        COMM_SERIAL.println("DFL: " + (String) heater_power);
        return;
      }
      if (input.charAt(0) == '0' && input.length() == 1) {
        COMM_SERIAL.println("DFL: Disabled heater.");
        return;
      }
      uint16_t power = input.toInt();
      if(power <= 0 || power > 100) {
        COMM_SERIAL.println("DFL: Provide a power value between 0 and 100.");
        return;
      }
      heater_power = (uint8_t)power;
      COMM_SERIAL.println("DFL: Set heater power to " + (String)heater_power + "%.");
    } else if (input == DFL_VOLTAGE_COMMAND) {
      COMM_SERIAL.readStringUntil('\n');
      float voltage = measure_voltage();
      COMM_SERIAL.println("DFL: Voltage: " + (String)voltage + "V");
    } else {
      COMM_SERIAL.readStringUntil('\n');
      COMM_SERIAL.println("DFL: Unknown command.");
    }
  }
}

void handle_step() {
  // Moving or homing
  if(stepMode != IDLE) {
    //Get the moving interval in microseconds and then
    // step the motor if it's time to move it.
    int32_t moving_interval = get_move_interval(stepMode);
    if(stepMode == HOMING) {
      // Handle homing.
      // We just reached the homing pos.
      // Set up our reference position so we
      // can target to move there.
      if(!digitalRead(LIM_PIN)) {
        set_mode(IDLE);
        step_index = HOMING_REF_POS;
        target     = 0;
        COMM_SERIAL.println("DFL: Finished homing.");
      }
      digitalWrite(DIR_PIN, HOMING_DIR);
    } else if (stepMode == MOVING) {
      // Handle moving.
      if(step_index > target) {
        // Start moving in.
        digitalWrite(DIR_PIN, DIR_IN);
      }
      if(step_index < target) {
        // Start moving out.
        digitalWrite(DIR_PIN, DIR_OUT);
      }
      if(step_index == target) {
        // We're done moving.
        set_mode(IDLE);
        COMM_SERIAL.println("DFL: Finished moving.");
      }
    }
   
    // Handle the step functions.

    // We need to divide `moving_interval` by 2 so we'll get
    // half-wave cycles between HIGH and LOW.
    // This function should be overflow safe.
    if(micros() - last_step_time > moving_interval / 2) {
      last_step_pin_state = !last_step_pin_state;
      digitalWrite(STEP_PIN, last_step_pin_state);
      last_step_time = micros();
      // If we have just started a new step,
      if(last_step_pin_state) {
        // Add one to step index if out,
        // subtract if in.
        if(direction == DIR_OUT) {
          step_index += 1;
        } else if(direction == DIR_IN) {
          step_index -= 1;
        } else {
          // ERROR
          // assert(false, "Unknown direction.");
        }
      }
    }
  } else {
    // Handle idling.
    // If we're currently idling,
    // and a new step_index has been asserted,
    // start moving.
    if(step_index != target) {
      COMM_SERIAL.println("DFL: Moving to " + (String)target + " steps.");
      set_mode(MOVING);
    }
  }
}

void handle_buttons() {
  int16_t button_val = analogRead(BUTTON_PIN);
  //Serial.println((String)button_val + ", abs up: " + (String)abs(button_val - BUTTON_UP));
  bool up_button_state = abs(button_val - BUTTON_UP) < BUTTON_TOLERANCE;
  bool down_button_state = abs(button_val - BUTTON_DOWN) < BUTTON_TOLERANCE;
  // If we just pressed the up button,
  // and the button debounce period has finished.
  if(up_button_state && !last_up_button_state
     && millis() - BUTTON_DEBOUNCE_MS > last_up_button_time)  {
    last_up_button_time = millis();
    set_target(target + BUTTON_STEP_SIZE);
    COMM_SERIAL.println("DFL: Button UP pressed. Moving out by " + (String)BUTTON_STEP_SIZE + " steps to " + (String)target + ".");
  }
  last_up_button_state = up_button_state;
  // If we just pressed the down button,
  // and the button debounce period has finished.
  if(down_button_state && !last_down_button_state
    && millis() - BUTTON_DEBOUNCE_MS > last_down_button_time)  {
    last_down_button_time = millis();
    set_target(target - BUTTON_STEP_SIZE);
    COMM_SERIAL.println("DFL: Button DOWN pressed. Moving in by " + (String)BUTTON_STEP_SIZE + " steps to " + (String)target + ".");
  }
  last_down_button_state = down_button_state;
}

void handle_heater() {
  // Provides a time in milliseconds of the current (wrapped) dew heater
  // period.
  uint32_t time_ms = millis() % DEW_HEATER_PERIOD_MS;
  // Signal is high if dew heater should be on.
  // Make sure we respect the dew heater active signal.
  uint8_t dew_heater_on = time_ms < (DEW_HEATER_PERIOD_MS * (heater_power / 100.0))
    ? ACTIVE_DEW_HEATER_STATE : 1 - ACTIVE_DEW_HEATER_STATE;
  digitalWrite(DEW_HEATER_PIN, dew_heater_on);
}

float measure_voltage() {
  uint16_t voltage_raw = analogRead(VOLTAGE_MEASURE_PIN);
  // Voltage in volts.
  float voltage = VOLTAGE_SUPPLY
    * (voltage_raw / (float)1023.0)
    * (((float)VOLTAGE_DIV_R2 + (float)VOLTAGE_DIV_R1) / (float)VOLTAGE_DIV_R1);
  return voltage;
}

