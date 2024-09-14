import json
import csv
import math

realtime_animation_s = 5
fps = 12

num_frames_refocus = 5

# Generate Input Frames
input_frames_file = open("input_frames.csv", 'r')

input_frames = csv.reader(input_frames_file)
frames = []
titles = []
for i, f in enumerate(input_frames):
    if i == 0:
        titles = f
    else:
        dict_frame = {}
        values = [float(x) for x in f] 
        for i, t in enumerate(titles):
            dict_frame[t] = values[i]
        frames.append(dict_frame)
print(titles, frames)


# Dictionary of filters with exposure time.
filters_exp = {
    "L" : 120,
    "R" : 30,
    "G" : 30,
    "B" : 30,
    "Ha" : 180,
    # "OIII" : 300,
    # "SII" : 300,
}

# The currently tracked offset value since the last autofocus.
af_offset_value = 0

# Calculates the derived focus position from the focal length.
def calculate_focus_pos(focal_length):
    # Math Function
    focus_pos = 13181 - 1502 * math.log(focal_length)
    return focus_pos

# Determines whether a frame should be autofocused.
def is_af_frame(frame_num):
    if frame_num == 0:
        return True
    if frame_num % num_frames_refocus == 0:
        return True
    return False

def generate_sequence():
    for i, f in enumerate(frames):
        ra = f['RA']
        dec = f['DEC']
        fl = f['FL']
        processing_string = f'Processing frame {i+1}/{len(frames)}: RA: {ra}, Dec: {dec}, Focal Length: {fl}mm'
        print("")
        print(processing_string)
        print("-" * len(processing_string))
        af_this_frame = is_af_frame(i)
        # Append AF tag.
        frames[i]["af"] = af_this_frame 
        if af_this_frame:
            frames[i]["offset"] = 0
            print("Autofocusing this frame. (Setting new focus offset to 0)")
        else:
            fp = calculate_focus_pos(fl)
            fp_last = calculate_focus_pos(frames[i-1]['FL'])
            offset = fp - fp_last
            frames[i]["offset"] = offset
            print(f'Focus Pos: {fp}, Focus Offset of: {offset}')
    
generate_sequence()
print(frames)
