using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ASCOM.LiamDaviesSprinterDFL.Switch
{
    public class Lens
    {
        public double minFocalLength;
        public double maxFocalLength;
        public string name;

        public Lens(double minFocalLength, double maxFocalLength, string name)
        {
            this.minFocalLength = minFocalLength;
            this.maxFocalLength = maxFocalLength;
            this.name = name;
        }

	public double clampLensFocalLength(double input) {
      	    if(input < this.minFocalLength) {
  		        return this.minFocalLength;
	        }
	        if(input > this.maxFocalLength) {
		        return this.maxFocalLength;
	        }
            return input;
	    }
    }

    internal static class LensHandler
    {

        public static Lens[] lenses = {
		new Lens(24, 105, "Canon EF 24-105mm f/4 L IS USM"),
		new Lens(17, 40, "Canon 17-40mm f/4 L USM"),
	        new Lens(16, 300, "Tamron 16-300mm f/3.5-6.3 Di II VC PZD")
	};

        public static string[] GetNames()
        {
            string[] names = new string[lenses.Length];
            for(int i =0; i < lenses.Length; i++)
            {
                names[i] = lenses[i].name;
            }
            return names;
        }

        public static int GetIndexOfLens(Lens lens)
        {
            return Array.IndexOf(lenses, lens);
        }

        public static Lens GetLensByName(String name)
        {
            return lenses.First(x => x.name == name);
        }
    }


}
