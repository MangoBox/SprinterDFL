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
            get
            {
                SendCommand("DFL:LIMIT", true);
                return _currentValue;
            }
            set {
                if (isInRange(value) && value == 1)
                {
                    SwitchHardware.step_controller.currentValue = 0;
                }
            }
        }
        public ParkedController (
            short switchID
         ) : base(switchID) {
         }
    }
}
