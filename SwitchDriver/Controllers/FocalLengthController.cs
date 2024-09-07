
namespace ASCOM.LiamDaviesSprinterDFL.Switch
{
    public class FocalLengthController : Controller {

        public override string switchName = "Focal Length";
        public override string switchDescription = "Controls the focal length of the Sprinter DFL system. [mm]";
        public override bool isBool = false;
        public override bool isWritable = true;
        public override double minValue;
        public override double maxValue;

        public override double currentValue {
            get {
                if(SwitchHardware.serialPort.IsOpen()) {
                    SwitchHardware.serialPort.WriteLine("DFL:GET");
                    String message = SwitchHardware.serialPort.ReadLine();
                    // Parse message and check values.
                    double value = Double.Parse(message);
                    return value;
                } else {
                    // Not open, just return the last value we set.
                    return currentValue;
                }
            }
            set {
                if(SwitchHardware.serialPort.IsOpen() && isInRange(value)) {
                    // Write focal length to serial port.
                    SwitchHardware.serialPort.writeLine(
                        String.format("DFL:FL {0}", value)); 
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
           this.minValue = minFL;
           this.maxValue = maxFL; 
         }
    }
}