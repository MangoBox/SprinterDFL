namespace ASCOM.LiamDaviesSprinterDFL.Switch
{
    public class ParkedController : Controller {

        public override string SwitchName { get { return "DFL Park"; } set { } }
        public override string SwitchDescription { get { return "Controls the park status of the DFL system."; } set { } }
        public override bool isBool { get { return true; } set { } }
        public override bool isWritable { get { return true; } set { } }
        public override double minValue { get { return 0; } set { } }
        public override double maxValue { get { return 1; } set { } }
	public override double stepSize { get { return 1; } set { } }
        public override double currentValue {
            get {
                if(SwitchHardware.serialPort.IsOpen) {
                    SwitchHardware.serialPort.WriteLine("DFL:LIMIT");
                    string message = SwitchHardware.serialPort.ReadLine();
                    // Parse message and check values.
                    double value = 0;
                    try
                    {
                        value = double.Parse(message);
			// Constrain value to 0 -> 1
			if (value != 0 && value != 1) {
			   return value;
			}
			//TODO: Raise error here.
			return value;
                    }
                    catch (System.FormatException exception)
                    {
                        value = 0;
                    }
                    return value;
                } else {
                    // Not open, just return the last value we set.
                    return 0;
                }
            }
            set {
                if(SwitchHardware.serialPort.IsOpen && isInRange(value) && value == 1) {
                    // Tell DFL system to home/park.
                    SwitchHardware.serialPort.WriteLine("DFL:HOME");
		    // Note that we don't set the current value here,
		    // as when the device finishes homing it should report
		    // a set park value from the getter anyway.
		    // Will this cause NINA to freak out?
                } else {
                    //TODO: Do nothing, and raise error?
                    return;
                }                
            }
        }
        public ParkedController (
            short switchID
         ) : base(switchID) {
         }
    }
}
