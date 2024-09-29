namespace ASCOM.LiamDaviesSprinterDFL.Switch
{
    public class MovingController : Controller {

        public override string SwitchName { get { return "DFL Moving"; } set { } }
        public override string SwitchDescription { get { return "Controls the moving status of the DFL system."; } set { } }
        public override bool isBool { get { return true; } set { } }
        public override bool isWritable { get { return true; } set { } }
        public override double minValue { get { return 0; } set { } }
        public override double maxValue { get { return 1; } set { } }
	    public override double stepSize { get { return 1; } set { } }

        public override void UpdateValue(string input_string)
        {
            double value = 0;
            try
            {
                value = double.Parse(input_string);
            }
            catch (System.FormatException exception)
            {

            }

            _currentValue = input_string == "MOVING" ? 1 : 0 ;
        }

        public override double currentValue {
            get {
                SendCommand("DFL:MODE", true);
                return _currentValue;
            }
            set {
                if(isInRange(value) && value == 0)
                {
                    //TODO: Do nothing, and raise error?
                    SendCommand("DFL:ABORT", false);
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
