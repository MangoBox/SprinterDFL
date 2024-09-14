import json

realtime_animation_s = 5
fps = 12

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
interframe_time = 30

frames = realtime_animation_s * fps

def generate_sequence():
    sum_per_frame = 0
    for filter, exp in filters_exp.items(): 
       sum_per_frame += exp
    print(f'{sum_per_frame} seconds per frame ({sum_per_frame/60} minutes)')
    total_time = (sum_per_frame + interframe_time) * frames
    print(f'Exposure duration: {total_time} seconds ({total_time/3600} hours)')
    print(f'{fps*total_time/frames/60} minutes required for 1 realtime second. ({fps*total_time/frames}:1)')

generate_sequence()
