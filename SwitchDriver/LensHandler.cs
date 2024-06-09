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
    }

    internal static class LensHandler
    {

        public static Lens[] lenses = { new Lens(24, 105, "Canon EF 24-105mm f/4 L IS USM"), new Lens(17, 40, "Canon 17-40mm f/4 L USM") };

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
