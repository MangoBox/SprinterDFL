namespace ASCOM.LiamDaviesSprinterDFL.Switch
{
    public class Voltage : Controller {

        public override string switchName = "Supply Voltage";
        public override string switchDescription = "Supply Voltage of the Sprinter DFL Board [V]";
        public override bool isBool = false;
        public override bool isWritable = false;
        public override double minValue = 0;
        public override double maxValue = 50;

        public override double currentValue {
            get {
                if(SwitchHardware.serialPort.IsOpen()) {
                    SwitchHardware.serialPort.WriteLine("DFL:VOLTAGE");
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
                // Do nothing, not settable.
                // Should we raise an error?
                return;
            }
        }
        public DewHeaterPower (
            short switchID,
         ) : base(switchID) {
         }
    }
}
