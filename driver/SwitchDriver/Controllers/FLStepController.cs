
using System.ComponentModel;
using System.Windows.Forms;

namespace ASCOM.LiamDaviesSprinterDFL.Switch
{
    public class FLStepController : Controller {

        public override string SwitchName { get { return "Focal Length Step Control"; } set { } }
        public override string SwitchDescription { get { return "Controls the stepper count of the Sprinter DFL system. [steps]"; } set { } }
        public override bool isBool { get { return false; } set { } }
        public override bool isWritable { get { return true; } set { } }
        public override double minValue { get { return _minSteps; } set { _minSteps = value; } }
        public override double maxValue { get { return _maxSteps; } set { _maxSteps = value; } }
	public override double stepSize { get { return 1; } set { } }

        public double _minSteps = 0;
        public double _maxSteps = 0;

        public override double currentValue {
            get {
                SendCommand("DFL:GET", true);
                // Return the current value of this for the moment.
                return _currentValue;
            }
            set
            {
                if (isInRange(value))
                {
                    SendCommand(string.Format("DFL:MOVE {0}", value), false);
                }
                else
                {
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
