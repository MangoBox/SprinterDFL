#include <Arduino.h>

#define LIMIT_PIN 7

void homeSystem();

// This is our current step position.
// Note that a current step position of -1 dictates that the
// system is homing, or needs to be homed.
int32_t currentStepPosition = -1;
int32_t stepTarget = 0;

uint32_t steps_per_sec = 100;

// Stepping variables.
uint32_t lastStepTime = 0;
uint32_t stepInterval = 1000 / steps_per_sec;

uint8_t stepArray[][4] =
{
  {1,0,0,1},
  {1,1,0,0},
  {0,1,1,0},
  {0,0,1,1}
};

void setup() {
  // put your setup code here, to run once:
  // Sets PB0, PB1, PB2 and PB3 as Outputs
  DDRB = 0b00001111;
  pinMode(LIMIT_PIN, INPUT_PULLUP);

  Serial.begin(115200);
  // Wait for Serial port to open.
  while(!Serial) {};

}


void loop() {
  
  

  if(currentStepPosition == -1) {
    // If we are not at the home position, home the system.
    homeSystem();
  } else {
    // If we are not at the home position,
    // continue cycling the system and targetting the next step.
    moveSystem();
  }
}

void moveSystem() {
  // If we have a step target, move to that position.
  // We are doing this asynchronously to allow for other operations to be performed.
  if(stepTarget > currentStepPosition) {
    if(millis() - lastStepTime >= stepInterval) {
      // Move to the next step.
      setStep(++currentStepPosition);
      // Update the last step time.
      lastStepTime = millis();
    }
  }

  if(stepTarget < currentStepPosition) {
    if(millis() - lastStepTime >= stepInterval) {
      // Move to the next step.
      setStep(--currentStepPosition);
      // Update the last step time.
      lastStepTime = millis();
    }
  }
}

int mod( int x, int y ){
  return x<0 ? ((x+1)%y)+y-1 : x%y;
}

void setStep(uint32_t step) {
  // Set the step position.
  step = mod(step, 4);
  PORTB = stepArray[step][0] << 3 | stepArray[step][1] << 2 | stepArray[step][2] << 1 | stepArray[step][3];
}

void homeSystem() {
  Serial.println("Homing system...");
  static int32_t homingSteps = 0;
  // Move to the end of the focal length travel.
  if(digitalRead(LIMIT_PIN) == LOW) {
    // If we are at the home position, set the current step position to 0.
    currentStepPosition = 0;
    Serial.println("System homed.");
    return;
  } 
  if(millis() - lastStepTime >= stepInterval) {
    // Move to the next step.
    setStep(--homingSteps);
    // Update the last step time.
    lastStepTime = millis();
  }
}