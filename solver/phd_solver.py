from astropy.io import fits

from guider import Guider
import sys
import time
import os
import datetime
import subprocess
import configparser


# This script reads the PHD debug folder, and feeds it into the ASTAP plate solver.
# It then returns the RA and DEC of the solved image.

host = "localhost"

astap_path = "C:\\Program Files\\astap\\astap.exe"
saved_image_path = ""
containing_folder = ""
new_file_name = ""

should_remove = False
date=datetime.datetime.now()

"""
with Guider(host) as guider:

    guider.Connect()

    # get the list of equipment profiles

    profiles = guider.GetEquipmentProfiles()

    for p in profiles:
        print(f"Found profile: {p}")

    selected_profile = profiles[0]
    print(f"Using profile: {selected_profile}")
    guider.ConnectEquipment(selected_profile)

    # print("Stopping guiding...")
    # guider.StopCapture()

    print("Starting capture...")
    current_pwd = os.getcwd()
    filename = guider.SaveImage()
    containing_folder = os.path.dirname(filename)
    new_file_name = 'phd-{date:%Y-%m-%d_%H-%M-%S}.fits'.format(date=date)
    print(f"Saved image to {filename}")
    print(f"Renaming {filename} to {new_file_name}...")
    saved_image_path = os.path.join(containing_folder, new_file_name)
    print(f"Full Image Path: {saved_image_path}")
    os.rename(filename, saved_image_path)

# We're done capturing.

"""

# Temp code to test the solver.
saved_image_path = "C:\\Users\\mango\\AppData\\Local\\phd2\\3.42-0000_2024-08-31_23-39-19_180.00s.fits"
containing_folder = "C:\\Users\\mango\\AppData\\Local\\phd2"

saved_output_path = os.path.join(containing_folder, 'output-{date:%Y-%m-%d_%H-%M-%S}.ini'.format(date=date))
subprocess.run([astap_path, 
                '-f', saved_image_path,
                '-o', saved_output_path,
                #'-r', '10',
                #'-fov', '25',
                '-r', '50'
                #'-spd', '0',
                #'-t', '0.01',
                #'-s', '300',
                #'-m', '5',
                ])

# Open output file.

# Finally, remove this image.
if(should_remove):
    print(f"Removing image {saved_image_path}...")
    os.remove(saved_image_path)
    print(f"Removing solving reults {saved_output_path}...")
    os.remove(saved_output_path)