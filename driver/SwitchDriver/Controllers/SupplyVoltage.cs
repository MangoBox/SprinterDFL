namespace ASCOM.LiamDaviesSprinterDFL.Switch
{
    public class SupplyVoltage : Controller {

        public override string SwitchName { get { return "Supply Voltage"; } set { } }
        public override string SwitchDescription { get { return "Supply Voltage of the Sprinter DFL Board [V]"; } set { } }
        public override bool isBool { get { return false; } set { } }
        public override bool isWritable { get { return false; } set { } }
        public override double minValue { get { return 0; } set { } }
        public override double maxValue { get { return 50; } set { } }

        public override double currentValue {
            get {
                if(SwitchHardware.serialPort.IsOpen) {
                    SwitchHardware.serialPort.WriteLine("DFL:VOLTAGE");
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
                // Do nothing, not settable.
                // Should we raise an error?
                return;
            }
        }
        public SupplyVoltage(
            short switchID
         ) : base(switchID) {
         }
    }
}
