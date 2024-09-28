namespace ASCOM.LiamDaviesSprinterDFL.Switch
{
    public class MovingController : Controller {

        public override string SwitchName { get { return "DFL Moving"; } set { } }
        public override string SwitchDescription { get { return "Controls the moving status of the DFL system."; } set { } }
        public override bool isBool { get { return true; } set { } }
        public override bool isWritable { get { return true; } set { } }
        public override double minValue { get { return 0; } set { } }
        public override double maxValue { get { return 1; } set { } }

        public override double currentValue {
            get {
                if(SwitchHardware.serialPort.IsOpen) {
                    SwitchHardware.serialPort.WriteLine("DFL:MODE");
                    string message = SwitchHardware.serialPort.ReadLine();
		    double value = message == "MOVING" ? 1 : 0;
		    return value;
                } else {
                    // Not open, just return the last value we set.
                    return 0;
                }
            }
            set {
                if(SwitchHardware.serialPort.IsOpen && isInRange(value)) {
                    // Tell DFL system to stop moving immediately.
                    SwitchHardware.serialPort.WriteLine("DFL:ABORT");
                } else {
                    //TODO: Do nothing, and raise error?
                    return;
                }                
            }
        }
        public MovingController (
            short switchID
         ) : base(switchID) {
         }
    }
}
