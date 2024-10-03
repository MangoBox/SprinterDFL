import sys
import json
import bezier
import numpy as np
import matplotlib.pyplot as plt

fps = 30

# Check if the command line argument is provided
if len(sys.argv) < 2:
    print("Please provide the path to the JSON file as a command line argument.")
    sys.exit(1)

# Get the file path from the command line argument
json_file_path = sys.argv[1]

try:
    # Read the JSON file
    with open(json_file_path) as file:
        data = json.load(file)

    # Access the keyframes.
    keyframes = data['sheetsById']['Camera']['sequence']['tracksByObject']['Keyframes']['trackData']
    # Access the tracks
    tracks = data['sheetsById']['Camera']['sequence']['tracksByObject']['Keyframes']['trackIdByPropPath']
    # Grab the IDs of the JSON objects
    ids = [tracks['[\"dec\"]'], tracks['[\"ra\"]'], tracks['[\"focalLength\"]']]
    # Get the keyframe list
    track_kfs = [keyframes[id] for id in ids]
    #print(kfs)

    # Get the keyframe list for each property
    for track in track_kfs:
        print(track["__debugName"])
        times = [t["position"] for t in track["keyframes"]]
        values = [t["value"] for t in track["keyframes"]]
        #print(f"Time: {times}, Value: {values}")
        curve = bezier.Curve([times, values], degree=len(times)-1)
        frames = fps * (times[-1] - times[0])
        times_sampled = []
        pos_sampled = []
        for f in range(int(frames)):
            t = f / fps + times[0]
            print(f"Frame: {f}, Time: {t}, Value: {curve.evaluate(t)[1]}")
            times_sampled.append(t)
            pos_sampled.append(curve.evaluate(t)[1].item())
        plt.plot(times_sampled,pos_sampled)
        plt.show()
        

    #print(keyframes)
    # Do something with the keyframes object
    #for k in keyframes:
        

except FileNotFoundError:
    print(f"File '{json_file_path}' not found.")
    sys.exit(1)

except json.JSONDecodeError:
    print(f"Invalid JSON format in file '{json_file_path}'.")
    sys.exit(1)