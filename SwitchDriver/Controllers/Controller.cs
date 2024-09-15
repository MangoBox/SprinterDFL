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

        // Current value requires overriding.
        public abstract double currentValue { get; set; }

        // Constructor
        public Controller(
            short switchID
        )
        {
            SwitchID = switchID;
        }

        public bool isInRange(double value) {
            return value <= maxValue && value >= minValue;
        }
    }
}