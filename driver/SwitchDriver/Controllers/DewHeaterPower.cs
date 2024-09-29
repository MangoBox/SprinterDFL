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

        public override double currentValue
        {
            get
            {
                SendCommand("DFL:HEATER", true);
                // Return the current value of this for the moment.
                return _currentValue;
            }
            set
            {
                if (isInRange(value))
                {
                    SendCommand(string.Format("DFL:HEATER {0}", value), false);
                }
                else
                {
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
