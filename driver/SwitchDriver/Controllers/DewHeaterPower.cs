namespace ASCOM.LiamDaviesSprinterDFL.Switch
{
    public class DewHeaterPower : Controller {

        public override string SwitchName { get { return "Dew Heater Power"; } set { } }
        public override string SwitchDescription { get { return "Controls the inbuilt Dew Heater's power [%]"; } set { } }
        public override bool isBool { get { return false; } set { } }
        public override bool isWritable { get { return true; } set { } }
        public override double minValue { get { return 0; } set { } }
        public override double maxValue { get { return 100; } set { } }
	public override double stepSize { get { return 1; } set { } }

        public override double currentValue {
            get {
                if(SwitchHardware.serialPort.IsOpen) {
                    SwitchHardware.serialPort.WriteLine("DFL:HEATER");
                    string message = SwitchHardware.serialPort.ReadLine();
                    // Parse message and check values.
                    double value = 0;
                    try
                    {
                        value = double.Parse(message);
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
                if(SwitchHardware.serialPort.IsOpen && isInRange(value)) {
                    // Write focal length to serial port.
                    SwitchHardware.serialPort.WriteLine(
                        string.Format("DFL:HEATER {0}", value)); 
                    //TODO: Handle errors if not okay.
                    currentValue = value;
                } else {
                    //TODO: Do nothing, and raise error?
                    return;
                }                
            }
        }
        public DewHeaterPower (
            short switchID
         ) : base(switchID) {
         }
    }
}
