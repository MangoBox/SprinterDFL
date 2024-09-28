using System;

namespace ASCOM.LiamDaviesSprinterDFL.Switch
{
    public abstract class Controller
    {
        public short SwitchID;
        public abstract string SwitchName { get; set; }
        public abstract string SwitchDescription { get; set; }
        public abstract bool isBool { get; set; }
        public abstract bool isWritable { get; set; }
        public abstract double minValue { get; set; }
        public abstract double maxValue { get; set; }
	public abstract double stepSize { get; set; }
        // Current value requires overriding.
        public abstract double currentValue { get; set; }

        // Constructor
        public Controller(
            short switchID
        )
        {
            SwitchID = switchID;
	    if (isBool && (stepSize != 1 || minValue != 0 || maxValue != 1)) {
	        throw new DriverException("Did not meet requirements to be registered as a boolean switch.");
	    }
        }

        public bool isInRange(double value) {
            return value <= maxValue && value >= minValue;
        }

	public double clampRange(double value) {
	   if isInRange(value) {
              return value;
	   } else if (value >= maxValue) {
	      return maxValue;
	   } else if (value <= minValue) {
	      return minValue;
	   }
	   // TODO: Raise error
	   return value;
	}
    }
}
