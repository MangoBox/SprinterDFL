
namespace ASCOM.LiamDaviesSprinterDFL.Switch
{
    public class FLStepController : Controller {

        public override string SwitchName { get { return "Focal Length Step Control"; } set { } }
        public override string SwitchDescription { get { return "Controls the stepper count of the Sprinter DFL system. [steps]"; } set { } }
        public override bool isBool { get { return false; } set { } }
        public override bool isWritable { get { return true; } set { } }
        public override double minValue { get { return _minSteps; } set { _minSteps = value; } }
        public override double maxValue { get { return _maxSteps; } set { _maxSteps = value; } }

        public double _minSteps = 0;
        public double _maxSteps = 0;

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
                        string.Format("DFL:MOVE {0}", value)); 
                    //TODO: Handle errors if not okay.
                    currentValue = value;
                } else {
                    //TODO: Do nothing, and raise error?
                    return;
                }
            }
        }

        public FLStepController (
            short switchID,
            double maxSteps
         ) : base(switchID) {
           this._minSteps = 0;
           this._maxSteps = maxSteps;
         }
    }
}
