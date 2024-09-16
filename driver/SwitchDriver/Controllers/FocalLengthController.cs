
namespace ASCOM.LiamDaviesSprinterDFL.Switch
{
    public class FocalLengthController : Controller {

        public override string SwitchName { get { return "Focal Length Control"; } set { } }
        public override string SwitchDescription { get { return "Controls the focal length of the Sprinter DFL system. [mm]"; } set { } }
        public override bool isBool { get { return false; } set { } }
        public override bool isWritable { get { return true; } set { } }
        public override double minValue { get { return _minValue; } set { _minValue = value; } }
        public override double maxValue { get { return _maxValue; } set { _maxValue = value; } }

        public double _minValue = 0;
        public double _maxValue = 0;

        public override double currentValue {
            get {
                if(SwitchHardware.serialPort.IsOpen) {
                    SwitchHardware.serialPort.WriteLine("DFL:GET");
                    string message = SwitchHardware.serialPort.ReadLine();
                    SwitchHardware.LogMessage("GetSwitchValue", "Received Serial Message: " + message);
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
                        string.Format("DFL:FL {0}", value)); 
                    //TODO: Handle errors if not okay.
                    currentValue = value;
                } else {
                    //TODO: Do nothing, and raise error?
                    return;
                }
            }
        }

        public FocalLengthController (
            short switchID,
            double minFL,
            double maxFL
         ) : base(switchID) {
           this._minValue = minFL;
           this._maxValue = maxFL; 
         }
    }
}