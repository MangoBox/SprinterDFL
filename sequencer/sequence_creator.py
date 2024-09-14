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
            offset = round(fp - fp_last)
            frames[i]["offset"] = offset
            print(f'Focus Pos: {fp}, Focus Offset of: {offset}')
        # Now, determine whether we should slew this frame.
        # We always need to slew on the first frames, or whenever RA or DEC changes.
        slew_this_frame = True if i == 0 else f['RA'] != frames[i-1]['RA'] or f['DEC'] != frames[i-1]['DEC']
        frames[i]['slew'] = slew_this_frame
        if slew_this_frame:
            print("Slewing required this frame.")
    return frames

def format_time(seconds):
    if seconds < 60:
        return f'{seconds:.2f}s'
    elif seconds < 60 * 60:
        whole_minutes = seconds // 60
        remaining_seconds = seconds - (whole_minutes * 60)
        return f'{whole_minutes}min {remaining_seconds:.0f}s'
    else:
        whole_hours = seconds // 3600
        remaining_seconds = seconds - (whole_hours * 3600)
        remaining_minutes = remaining_seconds // 60
        remaining_seconds -= remaining_minutes * 60
        return f'{whole_hours}h {remaining_minutes}min {remaining_seconds:.0f}s'

def calculate_sequence_time(sequence):
    # Time to switch filters, restart guiding,
    # download images, etc. per frame.
    inter_frame_time = 5
    slew_time = 10
    af_time = 30
    
    total_time = 0
    for f in frames:
        if f["af"]:
            total_time += af_time
        if f['slew']:
            total_time += slew_time
        for fil in filters_exp.values():
            total_time += fil
        total_time += inter_frame_time
    print(format_time(total_time))

generate_sequence()
calculate_sequence_time(frames)
