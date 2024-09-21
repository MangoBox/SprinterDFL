import json
import csv
import math
import copy

camera_temperature = -15

realtime_animation_s = 5
fps = 12

num_frames_refocus = 5
focal_length_var_identifier = "FL"
switch_name = "FocalLength"
interval_fl_read_s = 0.5
# Generate Input Frames
input_frames_file = open("input_frames.csv", 'r')
always_slew = True

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
    # Note: In future, could we add dynamic gains to
    # account for different focal lengths?
    "L" :  {"number" : 5, "exposure": 120, "gain": 139, "offset": 20},
    "Red" :  {"number" : 1, "exposure": 30, "gain": 0, "offset": 20},
    "Green" :  {"number" : 1, "exposure": 30, "gain": 0, "offset": 20},
    "Blue" :  {"number" : 1, "exposure": 30, "gain": 0, "offset": 20},
    "Ha" : {"number" : 1, "exposure": 120, "gain": 0, "offset": 20},
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
        slew_this_frame = (True if i == 0 else f['RA'] != frames[i-1]['RA'] or f['DEC'] != frames[i-1]['DEC']) or always_slew
        frames[i]['slew'] = slew_this_frame
        if slew_this_frame:
            print("Slewing required this frame.")
        # Determine whether we need to zoom this frame.
        zoom_this_frame = True if i == 0 else f['FL'] != frames[i-1]['FL']
        frames[i]['zoom'] = zoom_this_frame
        if zoom_this_frame:
            print("Changing focal lengths required this frame.")
        
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
            total_time += fil["exposure"]
        total_time += inter_frame_time
    print(format_time(total_time))

id = 0
def get_id_num():
    global id
    # Increments a global ID counter.
    id += 1
    return str(id)

def decdeg2dms(dd):
   is_positive = dd >= 0
   dd = abs(dd)
   minutes,seconds = divmod(dd*3600,60)
   degrees,minutes = divmod(minutes,60)
   degrees = degrees if is_positive else -degrees
   return (degrees,minutes,seconds)

def decdeg2hms(dd):
   is_positive = dd >= 0
   dd = abs(dd)
   hrs_in = dd / 15
   minutes,seconds = divmod(hrs_in*3600,60)
   hours,minutes = divmod(minutes,60)
   hours = hours if is_positive else -hours
   return (hours,minutes,seconds)

def create_object(type, init_base_id=True, init_conditions=True, init_items=True, init_triggers=False):
    if init_triggers:
        assert init_items and init_conditions, "Triggers cannot be initialized without conditions and items."
    if init_items:
        assert init_conditions, "Items cannot be initialized without conditions."
    obj = {}
    obj["$id"] = get_id_num() if init_base_id else None
    obj["IsExpanded"] = False
    obj["ErrorBehavior"] = 0
    obj["$type"] = type
    obj["Conditions"] = {
        "$type": "System.Collections.ObjectModel.ObservableCollection`1[[NINA.Sequencer.Conditions.ISequenceCondition, NINA.Sequencer]], System.ObjectModel",
        "$id": get_id_num() if init_conditions else None,
        "$values": []
    }
    obj["Items"] = {
        "$type": "System.Collections.ObjectModel.ObservableCollection`1[[NINA.Sequencer.Conditions.ISequenceCondition, NINA.Sequencer]], System.ObjectModel",
        "$id": get_id_num() if init_items else None,
        "$values": []
    }
    obj["Triggers"] = {
        "$type": "System.Collections.ObjectModel.ObservableCollection`1[[NINA.Sequencer.Conditions.ISequenceCondition, NINA.Sequencer]], System.ObjectModel",
        "$id": get_id_num() if init_triggers else None,
        "$values": []
    }
    return obj

# This checks any missing IDs in objects and updates them as nessecary.
def update_obj_ids(obj):
    if obj["Conditions"]["$id"] is None:
        obj["Conditions"]["$id"] = get_id_num()
    if obj["Items"]["$id"] is None:
        obj["Items"]["$id"] = get_id_num()
    if obj["Triggers"]["$id"] is None:
        obj["Triggers"]["$id"] = get_id_num()

def create_fl_var_init_obj(parent_id, starting_value):
    var_obj = create_object("WhenPlugin.When.SetVariable, WhenPlugin",
        init_base_id=True, init_conditions=False, init_items=False, init_triggers=False)
    var_obj["Parent"] = {'$ref': parent_id}
    var_obj["Variable"] = None
    var_obj["OValuExpr"] = None
    var_obj["OriginalDefinition"] = str(starting_value) # What does this mean?
    var_obj["Definition"] = str(starting_value) # What does this mean?
    var_obj["Identifier"] = focal_length_var_identifier
    return var_obj

def create_fl_var_set_obj(parent_id, value):
    var_obj = create_object("WhenPlugin.When.ResetVariable, WhenPlugin",
        init_base_id=True, init_conditions=False, init_items=False, init_triggers=False)
    var_obj["Parent"] = {'$ref': parent_id}
    var_obj["Variable"] = focal_length_var_identifier
    var_obj["CValuExpr"] = None
    var_obj["Expr"] = {
        "$id" : get_id_num(),
        "$type": "WhenPlugin.When.Expr, WhenPlugin",
        "Expression": str(value),
        "Type": None
    }
    return var_obj

def create_seq_start_obj(parent_id):
    start_obj = create_object("NINA.Sequencer.Container.SequentialContainer, NINA.Sequencer",
        init_base_id=True, init_conditions=True, init_items=True, init_triggers=False)
    start_obj["Name"] = "Start Items"
    start_obj["Parent"] = {'$ref': parent_id}
    start_obj["Strategy"] = {"$type": "NINA.Sequencer.Container.ExecutionStrategy.SequentialStrategy, NINA.Sequencer"}
    # Add in the start items here.
    
    # Set Camera Cooling
    cool_camera = create_object("NINA.Sequencer.SequenceItem.Camera.CoolCamera, NINA.Sequencer")
    cool_camera["Parent"] = {'$ref': parent_id}
    cool_camera["Temperature"] = camera_temperature
    cool_camera["Duration"] = 0
    update_obj_ids(cool_camera)
    start_obj["Items"]["$values"] = [cool_camera]

    # Unpark mount.
    unpark = create_object("NINA.Sequencer.SequenceItem.Telescope.UnparkScope, NINA.Sequencer")
    unpark["Parent"] = {'$ref': parent_id}
    update_obj_ids(unpark)
    start_obj["Items"]["$values"].append(unpark)

    # Set sidereal tracking.
    sidereal = create_object("NINA.Sequencer.SequenceItem.Telescope.SetTracking, NINA.Sequencer")
    sidereal["Parent"] = {'$ref': parent_id}
    sidereal["TrackingMode"] = 0
    update_obj_ids(sidereal)
    start_obj["Items"]["$values"].append(sidereal)

    update_obj_ids(start_obj)
    return start_obj
    
def create_seq_end_obj(parent_id):
    end_obj = create_object("NINA.Sequencer.Container.SequentialContainer, NINA.Sequencer",
        init_base_id=True, init_conditions=True, init_items=True, init_triggers=False)
    end_obj["Name"] = "End Items"
    end_obj["Parent"] = {'$ref': parent_id}
    end_obj["Strategy"] = {"$type": "NIA.Sequencer.Container.ExecutionStrategy.SequentialStrategy, NINA.Sequencer"}

    # Add in the start items here.

    # Set stopped tracking.
    stopped_tracking = create_object("NINA.Sequencer.SequenceItem.Telescope.SetTracking, NINA.Sequencer")
    stopped_tracking["Parent"] = {'$ref': parent_id}
    stopped_tracking["TrackingMode"] = 5
    update_obj_ids(stopped_tracking)
    end_obj["Items"]["$values"].append(stopped_tracking)

    update_obj_ids(end_obj)
    return end_obj

# This function creates a focal length object.
# It will automatically encapsulate the loop and
# checking behaviour in it.
def create_focal_length_object(parent, fl_value):
    # Create a container for everything to go into.
    container = create_object("NINA.Sequencer.Container.SequentialContainer, NINA.Sequencer",
        init_base_id=True, init_conditions=True, init_items=True, init_triggers=False)
    container["Name"] = f"Set Focal Length to {fl_value}mm"
    container["Parent"] = {'$ref': parent}
    container["Strategy"] = {"$type": "NINA.Sequencer.Container.ExecutionStrategy.SequentialStrategy, NINA.Sequencer"}
    container_id = container["$id"]
    # Set our initial variable value.
    # This should only be done once.
    var_set = create_fl_var_set_obj(container_id, fl_value)
    container["Items"]["$values"].append(var_set)
    # Now, tell the switch to move to the new focal length.
    switch_set = create_object("WhenPlugin.When.SetSwitchValue, WhenPlugin")
    switch_set["SwitchIndex"] = 0 # We might need to dynamically update this based on the ASCOM driver.
    switch_set["Parent"] = {'$ref': container_id}
    switch_set["ValueExpr"] = {
        "$id": get_id_num(),
        "$type": "WhenPlugin.When.Expr, WhenPlugin",
        "Expression": focal_length_var_identifier,
        "Type": None
    }
    update_obj_ids(switch_set)
    container["Items"]["$values"].append(switch_set)
    # Now, loop until the switch is done moving.
    # We will need to wait here until it is done.
    loop = create_object( "NINA.Sequencer.Container.SequentialContainer, NINA.Sequencer",
                         init_base_id=True, init_conditions=True, init_items=False, init_triggers=False)
    loop["Parent"] = {'$ref': container_id}
    loop["Name"] = f"Wait for Focal Length Change to {fl_value}mm"
    loop["Strategy"] = {
        "$type": "NINA.Sequencer.Container.ExecutionStrategy.SequentialStrategy, NINA.Sequencer"
    }
    loop_id = loop["$id"]
    # Add in loop condition.
    loop_condition = create_object("WhenPlugin.When.LoopWhile, WhenPlugin",
        init_base_id=True, init_conditions=False, init_items=False, init_triggers=False)
    loop_condition["Parent"] = {'$ref': loop_id}
    loop_condition["Predicate"] = None
    loop_condition["PredicateExpr"] = {
        "$id": get_id_num(),
        "$type": "WhenPlugin.When.Expr, WhenPlugin",
        "Expression": f"{switch_name} != {focal_length_var_identifier}", # Could change this to Not(SwitchIsMoving) later
        "Type": None
    }
    loop["Conditions"]["$values"] = [loop_condition]

    # Now, let's add our time span to wait.
    time_wait = create_object("NINA.Sequencer.SequenceItem.Utility.WaitForTimeSpan, NINA.Sequencer")
    time_wait["Parent"] = {'$ref': loop_id}
    time_wait["Time"] = interval_fl_read_s
    loop["Items"]["$values"].append(time_wait)

    update_obj_ids(loop)
    container["Items"]["$values"].append(loop)
    update_obj_ids(container)
    return container

def create_sequence_json(frames):
    # Creates base JSON object.
    sequence = create_object("NINA.Sequencer.Container.SequenceRootContainer, NINA.Sequencer")
    strategy = {}
    strategy['$type'] = "NINA.Sequencer.Container.ExecutionStrategy.SequentialStrategy, NINA.Sequencer"
    sequence["Strategy"] = strategy
    sequence["Name"] = "SprinterDFL Sequence" # Update sequence name here
    sequence["Parent"] = None
    # Items object. Actual sequence content in here.
    values = []
    # Start area container.
    base_container = create_object(None, init_conditions=False, init_items=False, init_triggers=False)
    base_container['Parent'] = {'$ref': "1"} # If sequence setup changes, will need to update.
    base_container['Strategy'] = {"$type": "NINA.Sequencer.Container.ExecutionStrategy.SequentialStrategy, NINA.Sequencer"}
    # Start container.
    start_container = copy.deepcopy(base_container)
    start_container["$id"] = get_id_num()
    start_container["Name"] = "Start"
    start_container["Conditions"]["$id"] = get_id_num() # Update ID.
    start_container["Items"]["$id"] = get_id_num() # Update ID.
    start_item = create_seq_start_obj(start_container["$id"])
    start_container["Items"]["$values"] = [start_item]
    start_container["Triggers"]["$id"] = get_id_num() # Update ID.
    start_container["$type"] = "NINA.Sequencer.Container.StartAreaContainer, NINA.Sequencer"

    values.append(start_container)
    # Target Area Container.
    target_area_container = copy.deepcopy(base_container)
    target_area_id = get_id_num()
    target_area_container["$id"] = target_area_id
    target_area_container["Name"] = "Targets"
    target_area_container["Conditions"]["$id"] = get_id_num() # Update ID.
    target_area_container["Items"]["$id"] = get_id_num() # Update ID.
    target_area_container["$type"] = "NINA.Sequencer.Container.TargetAreaContainer, NINA.Sequencer"
    
    target_items = []
    var_init_obj = create_fl_var_init_obj(target_area_id, frames[0]['FL'])
    target_items.append(var_init_obj)


    for i, f in enumerate(frames):
        container = create_object("NINA.Sequencer.Container.DeepSkyObjectContainer, NINA.Sequencer",
                                  init_base_id=False, init_conditions=False, init_items=False, init_triggers=False)
        frame_id = get_id_num()
        print(f"Adding frame {i+1}/{len(frames)} to sequence. ID: {frame_id}")
        container['$id'] = frame_id
        container['Strategy'] = {"$type": "NINA.Sequencer.Container.ExecutionStrategy.SequentialStrategy, NINA.Sequencer"}
        container_name = f"Frame {str(i+1) + "/" + str(len(frames)):<10} RA: {f['RA']:<10} DEC: {f['DEC']:<10} FL: {str(f['FL']) + "mm"}"
        container['Name'] = container_name
        container['Parent'] = {'$ref': target_area_id}
        container["Conditions"]["$id"] = get_id_num() # Update ID since we didn't do it on container init.
        container["Items"]["$id"] = get_id_num() # Update ID since we didn't do it on container init.
        target = create_object("NINA.Astrometry.InputTarget, NINA.Astrometry")
        target["PositionAngle"] = 0 # Update later if we want positional angle.
        target["TargetName"] = f"Frame {i+1}/{len(frames)}"
        # Convert RA and DEC to hms and dms.
        # RA is in hours, DEC is in degrees.
        (ra_hrs, ra_min, ra_sec) = decdeg2hms(f['RA'] * 15)
        (dec_deg, dec_min, dec_sec) = decdeg2dms(f['DEC'])
        # Handle negative dec values
        is_neg_dec = dec_deg < 0
        dec_deg = abs(dec_deg)

        target["InputCoordinates"] = {
            "$id": get_id_num(),
            "$type": "NINA.Astrometry.InputCoordinates, NINA.Astrometry",
            "RAHours": ra_hrs,
            "RAMinutes": ra_min,
            "RASeconds": ra_sec,
            "NegativeDec": is_neg_dec,
            "DecDegrees": dec_deg,
            "DecMinutes": dec_min,
            "DecSeconds": dec_sec,
        }
        update_obj_ids(target)
        container["Target"] = target
        seq_tasks = []

        # If we need to slew, do it here.
        if f["slew"]:
            slew = create_object("NINA.Sequencer.SequenceItem.Telescope.SlewScopeToRaDec, NINA.Sequencer")
            slew["Parent"] = {'$ref': frame_id}
            slew["Coordinates"] = {
                "$id": get_id_num(),
                "$type": "NINA.Astrometry.InputCoordinates, NINA.Astrometry",
                "RAHours": ra_hrs,
                "RAMinutes": ra_min,
                "RASeconds": ra_sec,
                "NegativeDec": is_neg_dec,
                "DecDegrees": dec_deg,
                "DecMinutes": dec_min,
                "DecSeconds": dec_sec,
            }
            update_obj_ids(slew)
            seq_tasks.append(slew)

        # Now, we add the instructions for this frame.
        # Add focus offset instructions
        if f["offset"] != 0:
            mfr = create_object("NINA.Sequencer.SequenceItem.Focuser.MoveFocuserRelative, NINA.Sequencer")
            mfr["RelativePosition"] = f["offset"]
            mfr["Parent"] = {'$ref': frame_id}
            update_obj_ids(mfr)
            seq_tasks.append(mfr)

        # If we need to autofocus, do it here.
        if f["af"]:
            af = create_object("NINA.Sequencer.SequenceItem.Autofocus.RunAutofocus, NINA.Sequencer")
            af["Parent"] = {'$ref': frame_id}
            update_obj_ids(af)
            seq_tasks.append(af)

        if f["zoom"]:
            fl_obj = create_focal_length_object(frame_id, f["FL"])
            seq_tasks.append(fl_obj)

        # Start autoguiding.
        start_autoguiding = create_object("NINA.Sequencer.SequenceItem.Guider.StartGuiding, NINA.Sequencer")
        start_autoguiding["Parent"] = {'$ref': frame_id}
        update_obj_ids(start_autoguiding)
        seq_tasks.append(start_autoguiding)

        # Add exposures for each filter.
        for filter in filters_exp.keys():
            # Create a new container for this filter.
            filter_container = copy.deepcopy(base_container)
            filter_container["$id"] = get_id_num()
            filter_container["Name"] = f"Expose {filter} ({filters_exp[filter]['number']}x{filters_exp[filter]['exposure']}s)"
            filter_container["Conditions"]["$id"] = get_id_num() # Update ID.
            filter_container["Items"]["$id"] = get_id_num()
            filter_container["$type"] = "NINA.Sequencer.Container.SequentialContainer, NINA.Sequencer"
            # Now, add items to the filter container.
            # Add filter change.
            filter_change = create_object("NINA.Sequencer.SequenceItem.FilterWheel.SwitchFilter, NINA.Sequencer")
            filter_change["Filter"] = {
                "$id": get_id_num(),
                "$type": "NINA.Equipment.Filter.Filter, NINA.Equipment",
                "_name": filter
            }
            filter_change["Parent"] = {'$ref': filter_container["$id"]}
            update_obj_ids(filter_change)
            filter_container["Items"]["$values"] = [filter_change]
            # Add exposure.
            exposure = create_object("NINA.Sequencer.SequenceItem.Imaging.TakeManyExposures, NINA.Sequencer")
            exposure["Parent"] = {'$ref': filter_container["$id"]}
            exposure["Name"] = "Take Many Exposures"
            exposure['Conditions'] = {
                "$type": "System.Collections.ObjectModel.ObservableCollection`1[[NINA.Sequencer.Conditions.ISequenceCondition, NINA.Sequencer]], System.ObjectModel",
                "$id": get_id_num(),
                "$values": [
                    {
                        "$id": get_id_num(),
                        "$type": "NINA.Sequencer.Conditions.LoopCondition, NINA.Sequencer",
                        "Parent": {'$ref': exposure["$id"]},
                        "CompletedIterations": 0,
                        "Iterations": filters_exp[filter]['number']
                    }
                ]
            }
            exposure["Items"] = {
                "$type": "System.Collections.ObjectModel.ObservableCollection`1[[NINA.Sequencer.Container.ISequenceItem, NINA.Sequencer]], System.ObjectModel",
                "$id": get_id_num(),
                "$values": [
                    {
                        "$id": get_id_num(),
                        "$type": "NINA.Sequencer.SequenceItem.Imaging.TakeExposure, NINA.Sequencer",
                        "ExposureTime": filters_exp[filter]['exposure'],
                        "Gain": filters_exp[filter]['gain'],
                        "Offset": filters_exp[filter]['offset'],
                        "Parent": {'$ref': exposure["$id"]},
                        "ImageType" : "LIGHT",
                        "ErrorBehavior": 0,
                        "Attempts": 1
                    }
                ]

            }
            update_obj_ids(exposure)
            filter_container["Items"]["$values"].append(exposure)

            update_obj_ids(filter_container)
            seq_tasks.append(filter_container)

        # Stop autoguiding.
        stop_autoguiding = create_object("NINA.Sequencer.SequenceItem.Guider.StopGuiding, NINA.Sequencer")
        stop_autoguiding["Parent"] = {'$ref': frame_id}
        update_obj_ids(stop_autoguiding)
        seq_tasks.append(stop_autoguiding)

        container["Items"]["$values"] = seq_tasks
        # Trigger IDs last.
        update_obj_ids(container)
        target_items.append(container)

    # Adding our sequence data here.

    target_area_container["Items"]["$values"] = target_items
    # We need to update triggers later.
    target_area_container["Triggers"]["$id"] = get_id_num() # Update ID.
    values.append(target_area_container)
    # End Container.
    end_container = copy.deepcopy(base_container)
    end_container["$id"] = get_id_num()
    end_container["Name"] = "End"
    end_container["Conditions"]["$id"] = get_id_num() # Update ID.
    end_container["Items"]["$id"] = get_id_num() # Update ID.

    end_obj = create_seq_end_obj(end_container["$id"])
    end_container["Items"]["$values"] = [end_obj]

    end_container["Triggers"]["$id"] = get_id_num() # Update ID.
    end_container["$type"] = "NINA.Sequencer.Container.EndAreaContainer, NINA.Sequencer"
    values.append(end_container)
    sequence["Items"]["$values"] = values
    # Triggers object.
    triggers = {}
    triggers["$id"] = get_id_num()
    triggers["$type"] = "System.Collections.ObjectModel.ObservableCollection`1[[NINA.Sequencer.SequenceItem.ISequenceItem, NINA.Sequencer]], System.ObjectModel"
    triggers["$values"] = []
    sequence["Triggers"] = triggers


    # Output and save sequence.
    with open("sequence_out.json", 'w') as fp:
        json.dump(sequence, fp, indent=2)


output_frames = generate_sequence()
calculate_sequence_time(frames)
create_sequence_json(output_frames)
