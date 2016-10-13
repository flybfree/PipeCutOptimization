import collections
# Global Mill variables

simulation_step = .1
# These are changed for the simulation
max_Length = 70.0
alt_Maximum_Length = 67.0
alt_Minimum_Length = 42.0
coil_Maximum_Length = 1000.0
coil_Minimum_Length = 800.0
# These are constraints that can be changed but should be not normally
mill_Max_Length = 83.0
millStop_BadLength = 40.0
tear_BadLength = 5.0
crossweld_BadLength =11.0
mill_Min_Length = 31.0
# stops per 10000 ft
millStop_Frequency = 4
tco_ClampEngageLength = 6.0

# These should not be changed as they are only modifeid in the program
running_Coil_Length = 0.0
crossweld_Location = 0.0

total_CoilLength = 0.0
total_PipeLength = 0.0
total_DefectLength = 0.0
total_Scrap =0.0

static_mill_stop = 0
no_live_stops =0
# Define defect info
# each defect has a location from the head, a length, and a type
# type 1 is a crossweld
# type 2 is a furnace tear specified from the steel mill 
# type 3 is a mill stop
Defect=collections.namedtuple("Defect",["location","length","defect_type"])
Pipe = collections.namedtuple("Pipe",["pipeid","length","defect_length"])
SummaryResult=collections.namedtuple("SummaryResult",["frequency","num_runs","num_stops","total_pipe_ft","total_scrap","total_count"])
RunResult = collections.namedtuple("RunResult",["num_stops","total_pipe_ft","total_scrap","pipe_count","pipe_group"])
PipeGroup = collections.namedtuple("PipeGroup",["line1_count","line1_length","line1_scrap","line2_count","line2_length",
                                                "line2_scrap","line3_count","line3_length","line3_scrap","line4_count","line4_length","line4_scrap",
                                                "pipe0_count","pipe0_length"])
Coil_Pipes = []
Pipe_Log=[]
coil_number = 0
pipe_number = 0

