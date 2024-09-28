
namespace ASCOM.LiamDaviesSprinterDFL.Switch
{
    public class FocalLengthController : Controller {
	
	// This focal length controller class is essentially a wrapper
	// for the FLStepController. This allows us to automatically perform
	// step movements without worrying about the actual focal length spacing
	// of the lens. 
        public override string SwitchName { get { return "Focal Length"; } set { } }
        public override string SwitchDescription { get { return "Controls the focal length of the Sprinter DFL system. [mm]"; } set { } }
        public override bool isBool { get { return false; } set { } }
        public override bool isWritable { get { return true; } set { } }
        public override double minValue { get { return _minValue; } set { _minValue = value; } }
        public override double maxValue { get { return _maxValue; } set { _maxValue = value; } }
	public override double stepSize { get { return 0.01; } set { } }
        public double _minValue = 0;
        public double _maxValue = 0;
	public FLStepController step_controller;
	
	// Converts focal length [mm] to a whole number of steps
	public int fl_to_steps(double focal_length) {
		return int(focal_length) / 1000;
	}

	// Converts a whole number of steps to focal length [mm]
	public double steps_to_fl(int steps) {
		return steps * 1000;
	}

        public override double currentValue {
            get {
		// Return the current converted focal length.
		return steps_to_fl(step_controller.currentValue);
            }
            set {
		// To set the current value, we need to
		// feed the existing step position into a correction function.
		// TODO: If the value is out of range, should we throw an error?
		double clamped_value = clampRange(value);
		step_controller.currentValue = fl_to_steps(clamped_value);
            }
        }

        public FocalLengthController (
            short switchID,
            double minFL,
            double maxFL,
	    FLStepController step_controller
         ) : base(switchID) {
           this._minValue = minFL;
           this._maxValue = maxFL; 
	   this.step_controller = step_controller;
         }
    }
}
