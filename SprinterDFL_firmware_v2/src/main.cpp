#include <Arduino.h>
#include <TimerOne.h>

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
#define DIR_OUT            LOW
#define DIR_IN             HIGH
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
#define DFL_REL_COMMAND     "DFL:REL"
#define DFL_GET_COMMAND     "DFL:GET"
#define DFL_HOME_COMMAND    "DFL:HOME"
#define DFL_ABORT_COMMAND   "DFL:ABORT"
#define DFL_HEATER_COMMAND  "DFL:HEATER"
#define DFL_VOLTAGE_COMMAND "DFL:VOLTAGE"
#define DFL_LIM_COMMAND     "DFL:LIMIT"
#define DFL_MODE_COMMAND    "DFL:MODE"

// Steps per second
#define HOMING_SPEED 200
#define MOVING_SPEED 500
#define IDLE_SPEED 0
#define ENABLED_WHEN_IDLE false

// Should we automatically resync to the home position
// whenever we hit the limit switch?
#define RESYNC_ON_LIMIT true
#define LIM_DEBOUNCE_MS 50

// Provides a more detailed serial debug option.
// During driver operation, this should be disabled.
// TODO: We could also set this up on a different SoftwareSerial or something.
#define SERIAL_DEBUG true

enum StepMode {
  HOMING,
  MOVING,
  IDLE
};

int32_t  step_index             = 0;
int32_t  target                 = 0;
bool     last_step_pin_state    = false;
uint8_t  heater_power           = 0;
bool     last_up_button_state   = false;
uint32_t last_up_button_time    = 0;
bool     last_down_button_state = false;
uint32_t last_down_button_time  = 0;
uint8_t  direction              = DIR_IN;
bool     new_state              = false;
bool     last_lim_switch_state  = false;
uint32_t last_lim_switch_time   = 0;

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

#include <TimerOne.h>

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
  print_debug("DFL: Beginning initialisation...");

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
 
  Timer1.initialize();
  Timer1.attachInterrupt(handle_step);
  set_mode(HOMING);
  print_debug("DFL: Started homing...");
}


void loop() {
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
  Timer1.setPeriod(get_move_interval(mode));
  if (mode != IDLE) {
    Timer1.start();
  } else {
    Timer1.stop();
  }
  // We can't write these serial values in the interrupt handler,
  // which this function is sometimes called from.
  // So, we set a flag to write them in the main loop.
  new_state = true;
}

void print_debug(String message) {
   // Will only print if debug mode is enabled.
   if(SERIAL_DEBUG) {
	Serial.println(message);
   }
}

void handle_input() {
  if(new_state) {
    new_state = false;
    switch(stepMode) {
      case MOVING:
        print_debug("DFL: MOVING");
        return;
      case HOMING:
        print_debug("DFL: HOMING");
        return;
      case IDLE:
        print_debug("DFL: IDLE");
        return;
      default:
        print_debug("DFL: Entered unknown state.");
        return;
    }
  }
  if(COMM_SERIAL.available() > 0) {
    // Does this work?
    String input = COMM_SERIAL.readStringUntil('\n');
    input.trim();
    String command = input;
    String arguments = "";
    // If there are arguments provided, split them.
    if(input.indexOf(' ') != -1) {
      command = input.substring(0, input.indexOf(' '));
      arguments = input.substring(input.indexOf(' ') + 1);
    }
   
    if(command == DFL_MOVE_COMMAND || command == DFL_REL_COMMAND) {
      if(arguments.length() == 0) {
        print_debug("DFL: No position provided.");
        return;
      }
      uint32_t move_pos = arguments.toInt();
      if(move_pos == 0 && command == DFL_REL_COMMAND) {
        print_debug("DFL: Could not parse position, or provided 0.");
        return;
      }
      // Sanity check move position.
      if(move_pos == step_index && command == DFL_MOVE_COMMAND) {
        debug_print("DFL: Already at that position.");
        return;
      }
      uint32_t new_target = command == DFL_MOVE_COMMAND ? move_pos : target + move_pos;
      //Set target position, and change to moving mode.
      set_target(new_target);
      print_debug("DFL: Set target to position " + (String)new_target);
      set_mode(MOVING);
    } else if (command == DFL_HOME_COMMAND) {
      // Home DFL
      // Clear the rest of the serial buffer since we don't need to read it.
      print_debug("DFL: Started homing.");
      set_mode(HOMING);
    } else if (command == DFL_ABORT_COMMAND) {
      print_debug("DFL: Aborted movement.");
      set_mode(IDLE);
      target = step_index;
    } else if (command == DFL_GET_COMMAND) {
      print_debug("DFL: " + (String)step_index + " (Target: " + (String)target + ")");
      COMM_SERIAL.println(step_index);
      print_mode();
    } else if (command == DFL_MODE_COMMAND) {
      if(arguments.length() != 0) {
        print_debug("DFL: Cannot set mode with this command.");
	return;
      }
      switch(stepMode) {
        case MOVING:
          print_debug("DFL: MOVING");
	  COMM_SERIAL.println("MOVING");
          return;
        case HOMING:
          print_debug("DFL: HOMING");
	  COMM_SERIAL.println("HOMING");
          return;
        case IDLE:
          print_debug("DFL: IDLE");
	  COMM_SERIAL.println("IDLE");
          return;
        default:
          print_debug("DFL: Entered unknown state.");
	  COMM_SERIAL.println("UNKNOWN");
          return;

    } else if (command == DFL_HEATER_COMMAND) {
      if (arguments.length() == 0) {
        print_debug("DFL: " + (String) heater_power);
	COMM_SERIAL.println(heater_power);
        return;
      }
      if (arguments.charAt(0) == '0' && arguments.length() == 1) {
        print_debug("DFL: Disabled heater.");
        return;
      }
      uint16_t power = arguments.toInt();
      print_debug("DFL: Set heater power to " + (String)heater_power + "%.");
      if(power <= 0 || power > 100) {
        print_debug("DFL: Provide a power value between 0 and 100.");
        return;
      }
      heater_power = (uint8_t)power;
    } else if (command == DFL_VOLTAGE_COMMAND) {
      float voltage = measure_voltage();
      print_debug("DFL: Voltage: " + (String)voltage + "V");
      COMM_SERIAL.println(voltage);
    } else if (command = DFL_LIM_COMMAND) {
      // Outputs whether the limit switch is currently depressed.
      uint8_t state = digitalRead(LIM_PIN);
      debug_print("DFL: Current limit switch state is " + (String)state);
      COMM_SERIAL.println(state);
    } else {
      print_debug("DFL: Unknown command.");
    }
  }
}

void handle_step() {
    if(stepMode == HOMING) {
      // Handle homing.
      // We just reached the homing pos.
      // Set up our reference position so we
      // can target to move there.
      if(!digitalRead(LIM_PIN)) {
        set_mode(IDLE);
        step_index = HOMING_REF_POS;
        target     = 0;
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
      }
      // If RESYNC_ON_LIMIT is enabled, let's resync
      // the position if we have hit the limit switch on an
      // inwards movement. This should let us resync when we
      // re-approach the inwards limit, without interfering when
      // we do outwards movements.
      if(RESYNC_ON_LIMIT) {
	if(direction == DIR_IN
	  && !digitalRead(LIM_PIN)
	  && !last_lim_switch_state
	  && millis() - LIM_DEBOUNCE_MS > last_lim_switch_time
	) {
          // Now, let's resync.
	  // First set tracking variables for ensuring we don't trigger
	  // multiple times and when we move out again.
	  last_lim_switch_state = true;
	  last_lim_switch_state = millis();
	  debug_print("DFL: Hit limit switch at position " + (String)step_index ". Resyncing to 0.");
	  step_index = 0;
	  // After we have reset our step limit,
	  // the controller will 'refind' the set target position.
	}
	// If our limit switch is no longer depressed,
	// set our state again.
	if(digitalRead(LIM_PIN)) {
	  last_lim_switch_state = false;
	}
      }
    }
    // Handle the step functions.
    last_step_pin_state = !last_step_pin_state;
    digitalWrite(STEP_PIN, last_step_pin_state);
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

void handle_buttons() {
  int16_t button_val = analogRead(BUTTON_PIN);
  bool up_button_state = abs(button_val - BUTTON_UP) < BUTTON_TOLERANCE;
  bool down_button_state = abs(button_val - BUTTON_DOWN) < BUTTON_TOLERANCE;
  // If we just pressed the up button,
  // and the button debounce period has finished.
  if(up_button_state && !last_up_button_state
     && millis() - BUTTON_DEBOUNCE_MS > last_up_button_time)  {
    last_up_button_time = millis();
    set_target(target + BUTTON_STEP_SIZE);
    debug_print("DFL: Button UP pressed. Moving out by " + (String)BUTTON_STEP_SIZE + " steps to " + (String)target + ".");
  }
  last_up_button_state = up_button_state;
  // If we just pressed the down button,
  // and the button debounce period has finished.
  if(down_button_state && !last_down_button_state
    && millis() - BUTTON_DEBOUNCE_MS > last_down_button_time)  {
    last_down_button_time = millis();
    set_target(target - BUTTON_STEP_SIZE);
    debug_print("DFL: Button DOWN pressed. Moving in by " + (String)BUTTON_STEP_SIZE + " steps to " + (String)target + ".");
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

