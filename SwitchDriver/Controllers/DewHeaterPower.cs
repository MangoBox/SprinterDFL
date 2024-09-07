namespace ASCOM.LiamDaviesSprinterDFL.Switch
{
    public class DewHeaterPower : Controller {

        public override string switchName = "Dew Heater Power";
        public override string switchDescription = "Controls the inbuilt Dew Heater's power [%]";
        public override bool isBool = false;
        public override bool isWritable = true;
        public override double minValue = 0;
        public override double maxValue = 100;

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
                        String.format("DFL:HEATER {0}", value)); 
                    //TODO: Handle errors if not okay.
                    currentValue = value;
                } else {
                    //TODO: Do nothing, and raise error?
                    return;
                }                
            }
        }
        public DewHeaterPower (
            short switchID,
         ) : base(switchID) {
         }
    }
}