using System;

namespace ASCOM.LiamDaviesSprinterDFL.Switch
{
    public abstract class Controller
    {
        public short SwitchID;
        public abstract string SwitchName;
        public abstract string SwitchDescription;
        public abstract bool isBool;
        public abstract bool isWritable;
        public abstract double minValue;
        public abstract double maxValue;
        
        // Current value requires overriding.
        public abstract double currentValue;

        // Constructor
        public Controller(
            short switchID,
        )
        {
            SwitchID = switchID;
        }

        public bool isInRange(double value) {
            return value <= maxValue && value >= minValue;
        }
    }
}
