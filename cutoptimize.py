import collections
import collections
import random
import math
import time
import millvar  # global simulation variables and datatypes are kept here

nextCoil_DefectList = {}
debugPrint = False
runPrint = 0
# set to 1 will generate millstops as part of coil creation
# set to 0 will randomly generate mill stops each time a coil is run
millvar.no_live_stops = 1

# parameter = 0 means no defects 1 is use defects
generate_defects = 0

if millvar.no_live_stops == 1:
    generate_defects = 0

newpipes = []
millvar.cutlist = []
millvar.nextbad = []
coilpipes = []

# a list of every pipe produced in the simulation
# the format of the pipeid indicates mill stop frequency,
# run number for the frequency, the coil number and the pipe number
#  XXYY ZZZZ AA
#                  XX = mill stop frequency per 10000 ft
#                  YY = the run/interation at the specified frequency
#                ZZZZ = the coil number from the run
#                  AA = the pipe number from the coil
masterpipes = []


# return amount of scrap based on defect length and pipelength
def calc_scrap(defect_len, pipe_len):
    if defect_len == millvar.tear_BadLength:
        scrap = defect_len
    if defect_len == millvar.crossweld_BadLength:
        scrap = defect_len * 2
    else:
        scrap = defect_len

    return scrap


######################################################################################
#  Get defects from previous Coil
#
#

def get_Prev_Coil_Defects():
    defectlist = []
    for key in nextCoil_DefectList:

        defect = nextCoil_DefectList[key]
        dLoc = int(defect.location)
        dLen = defect.length
        dType = defect.defect_type
        dLoc = dLoc + millvar.headChop
        # if defect location is less than zero then the defect position is now
        # zero and the length of the defect is shortend by the negative location amount
        #
        if dLoc < 0:
            dLen += dLoc
            dLoc = 0
        newdefect = millvar.Defect(dLoc, dLen, dType)

        defectid = dLoc
        if runPrint == 1:
            print("added from previous coil mill stop", newdefect)
        defectlist.append(newdefect)
        # print defectlist
        # for defect in defectlist:
        # print defect

    # print "new defectlist",defectlist

    return defectlist


################################################################################
# Load a coil to run
# inputs: coil , headChop(amount borrowed by previous coil)
# Returns defect list
def load_Coil(coil, headChop):
    coil_DefectList = {}
    running_Coil_Length = coil[0]
    crossweld_Location = coil[0]
    if debugPrint:
        print('\nLoad Coil- enter load_Coil')
        print('defects:', coil[1], millvar.tear_BadLength, ' ft',
              coil[2], millvar.tear_BadLength, ' ft',
              coil[3], millvar.tear_BadLength, ' ft   static mill stop at',
              coil[4], ' ft\n')

    # create defect at crossweld
    # newdefect = millvar.Defect(coil[0] + headChop, millvar.crossweld_BadLength, 1)
    newdefect = millvar.Defect(coil[0] + headChop, millvar.crossweld_BadLength, 1)
    # add defects that came from steel mill
    defectid = newdefect.location
    coil_DefectList[defectid] = newdefect

    if coil[1] > 0:
        newdefect = millvar.Defect(coil[1] + headChop, millvar.tear_BadLength, 2)
    else:
        newdefect = millvar.Defect(coil[1], millvar.tear_BadLength, 2)
    defectid = newdefect.location
    coil_DefectList[defectid] = newdefect

    if coil[2] > 0:
        newdefect = millvar.Defect(coil[2] + headChop, millvar.tear_BadLength, 2)
    else:
        newdefect = millvar.Defect(coil[2], millvar.tear_BadLength, 2)
    defectid = newdefect.location
    coil_DefectList[defectid] = newdefect

    if coil[3] > 0:
        newdefect = millvar.Defect(coil[3] + headChop, millvar.tear_BadLength, 2)
    else:
        newdefect = millvar.Defect(coil[3], millvar.tear_BadLength, 2)
    defectid = newdefect.location
    coil_DefectList[defectid] = newdefect
    if debugPrint:
        print('exit load_coil  defects: ', coil_DefectList)

    return coil_DefectList


################################################################################
# clean up the defect list by removing entries that are negative locations
# since they no longer matter
def clean_Defects(coil_DefectList):
    newdefects = []
    for key in coil_DefectList:
        defect = coil_DefectList[key]
        dLoc = int(defect.location)
        dLen = defect.length
        dType = defect.defect_type
        if dLoc >= 0:
            newdefect = millvar.Defect(dLoc, dLen, dType)
            newdefects.append(newdefect)

            # Rewrite list after cleanup
    coil_DefectList.clear()
    for defect in newdefects:
        defectid = defect.location
        if defectid > 0:
            coil_DefectList[defectid] = defect
    return coil_DefectList


# Get distance to closest defect
def get_ClosestDefect(coil_DefectList):
    # print('Defect list length = ', len(coil_DefectList))
    # print('get closest defect list = ',coil_DefectList)
    start = 1
    for key in coil_DefectList:
        defect = coil_DefectList[key]
        location = defect.location
        # debug_print(" Closest defect: key, location= "+str(key)+ ", " +str(location))
        if start == 1:
            if location > 0:
                closest = location
                start = 0
            else:
                pass
        if location > 0:
            if location < closest:
                closest = location
                dlength = defect.length
                start = 0

                # print coil_DefectList[closest]
    return coil_DefectList[closest]


def get_Next_Closest_Defect(closest, coil_DefectList):
    nextclosest = closest
    for key in coil_DefectList:
        defect = coil_DefectList[key]
        location = defect.location
        if location > 0:
            if location < closest:
                nextclosest = location
                dlength = defect.length
    # print coil_DefectList[closest]
    return coil_DefectList[nextclosest]


# Cut a pipe and add to list of created pipes
def cut_Pipe(pipe):
    cutlength = pipe.length
    defectlength = pipe.defect_length
    if cutlength > millvar.mill_Max_Length:
        print("cutlength", cutlength)

        print(millvar.cutlist)
        raise ValueError("bad length")
    newpipes.append(pipe)
    millvar.tco_PipeLength = 0
    print('cut pipe\n')
    return pipe


# create a mill stop defect and add to list of defects
def add_MillStop(coil_DefectList, current_coil_length):
    coil_DefectList = add_defect(coil_DefectList, 153, millvar.millStop_BadLength, 3)
    print('mill stop defect list-ams', coil_DefectList)

    return coil_DefectList


##
##return the total length of defects in current coil
def calc_total_fault_length(coil_DefectList):
    clean_Defects(coil_DefectList)
    total_defect_length = 0
    closest = get_ClosestDefect(coil_DefectList)
    return closest.length


##add a pipe to the current cutlist
def add_to_cutlist(cutlist, pipelen, def_len):
    pipe = millvar.Pipe('XCUT', pipelen, def_len)
    if pipelen <= millvar.mill_Max_Length:
        cutlist.append(pipe)

        # print(str(pipe.length) + "added to cutlist with " + str(pipe.defect_length) + " defect")
    else:
        raise ValueError(pipelen)
    return cutlist


def remove_defect(coil_DefectList, location):
    newdefects = []

    for key in coil_DefectList:
        defect = coil_DefectList[key]
        dLoc = int(defect.location)
        dLen = defect.length
        dType = defect.defect_type
        if dLoc == location:
            dLoc = 0
        oldDefect = millvar.Defect(dLoc, dLen, dType)
        newdefects.append(oldDefect)


        # Clear coil defect list before we rewrite it with updated information
    coil_DefectList.clear()
    # Rewrite defect list to reflect mill movement
    for defect in newdefects:
        defectid = defect.location
        if defectid > 0:
            coil_DefectList[defectid] = defect

    return coil_DefectList


def add_defect(coil_DefectList, location, length, dtype):
    newdefects = []
    new_defect = millvar.Defect(location, length, dtype)

    for key in coil_DefectList:
        defect = coil_DefectList[key]
        dLoc = int(defect.location)
        dLen = defect.length
        dType = defect.defect_type
        oldDefect = millvar.Defect(dLoc, dLen, dType)
        newdefects.append(oldDefect)
    newdefects.append(new_defect)

    # Clear coil defect list before we rewrite it with updated information
    coil_DefectList.clear()
    # Rewrite defect list to reflect mill movement
    for defect in newdefects:
        defectid = defect.location
        if defectid > 0:
            coil_DefectList[defectid] = defect

    return coil_DefectList


def shift_defect(coil_DefectList, offset):
    newdefects = []

    for key in coil_DefectList:
        defect = coil_DefectList[key]
        dLoc = int(defect.location) + offset
        dLen = defect.length
        dType = defect.defect_type
        oldDefect = millvar.Defect(dLoc, dLen, dType)

    newdefects.append(oldDefect)

    # Clear coil defect list before we rewrite it with updated information
    coil_DefectList.clear()
    # Rewrite defect list to reflect mill movement
    for defect in newdefects:
        defectid = defect.location
        if defectid > 0:
            coil_DefectList[defectid] = defect

    return coil_DefectList


def add_next_coil_mill_stops(headChop, coil_DefectList):
    if headChop > 0:
        coil_DefectList = add_defect(coil_DefectList, headChop, millvar.millStop_BadLength, 3)

    return coil_DefectList


def add_crossweld(headChop, coil_DefectList):
    if headChop > 0:
        coil_DefectList = add_defect(coil_DefectList, headChop, millvar.crossweld_BadLength, 1)

    return coil_DefectList


# Generate test coil data for simulation run defects here are furnace tears
def create_simulation_coil_list(generate_defects, num_coils):
    coillist = []
    for i in range(0, num_coils + 1):
        coil_length = random.randint(millvar.coil_Minimum_Length, millvar.coil_Maximum_Length)
        def_1 = random.randint(0, coil_length) * random.randint(0, 1) * generate_defects
        def_2 = random.randint(0, coil_length) * random.randint(0, 1) * generate_defects
        def_3 = random.randint(0, coil_length) * random.randint(0, 1) * generate_defects
        # def_4 is used to create coil based mill stops instead of random stops
        # using the no_live-stops flag
        addmillstop = random.randint(0, 10)
        if addmillstop <= 2:
            def_4 = random.randint(20, coil_length - 10)
        else:
            def_4 = 0
        coil = [coil_length, def_1, def_2, def_3, def_4]
        coillist.append(coil)

        coillist = [(823, 0, 800, 0, 0), (913, 113, 0, 359, 0), (814, 141, 0, 0, 0), (889, 0, 608, 81, 0),
                    (840, 313, 136, 0, 0),
                    (803, 476, 0, 0, 0), (963, 0, 0, 0, 0), (849, 0, 477, 0, 0), (902, 0, 383, 0, 0),
                    (946, 0, 104, 0, 845),
                    (977, 0, 0, 467, 0), (1000, 0, 0, 0, 0), (933, 0, 0, 720, 0), (863, 503, 651, 401, 0),
                    (940, 0, 631, 69, 0),
                    (843, 241, 0, 0, 382), (974, 96, 0, 350, 0), (929, 0, 0, 0, 0), (836, 0, 0, 0, 0),
                    (978, 0, 0, 739, 0),
                    (905, 0, 0, 0, 0), (976, 800, 485, 87, 756), (809, 188, 706, 0, 0), (837, 450, 0, 250, 0),
                    (806, 753, 529, 0, 76), (892, 463, 277, 0, 510), (966, 0, 303, 0, 0), (869, 0, 247, 0, 0),
                    (919, 553, 612, 225, 466), (864, 228, 475, 559, 0), (893, 51, 53, 0, 0)]

        # print(coillist)
        # coillist = [(831 ,  165 ,  0 ,  0 ,  60),(830 ,  0 ,  0 ,  0 ,  0)]
        # coillist = [(860.0 ,  0.0 ,  700.5 ,  0.0 ,  300.0),(830 ,  0 ,  654 ,  0 ,  0),(860 ,  0 ,  0 ,  0 ,  250)]
        # coillist =[(895, 0, 0, 0, 737), (812, 0, 0, 374, 525)]#, (933, 810, 448, 701, 0), (836, 747, 506, 332, 0)
        # coillist=[(916, 562, 306, 49, 0), (821, 452, 14, 420, 0), (840, 274, 194, 0, 0),
        #    (993, 280, 0, 0, 758), (992, 405, 0, 0, 946), (831, 5, 430, 746, 0),
        #    (885, 771, 0, 0, 0), (842, 732, 107, 551, 0), (939, 0, 0, 0, 0), (926, 0, 0, 143, 0),
        #    (814, 0, 0, 580, 0), (993, 0, 0, 387, 680), (899, 501, 0, 888, 312), (937, 0, 0, 81, 0),
        #    (899, 0, 531, 8, 0)]
    # coillist=[(937, 0, 400, 0, 110),(635.0, 324, 516, 0, 600),(635.0, 516, 416, 316, 100)]
    # coillist = [(800.700, 600, 500, 400, 100), (880, 0, 0, 0, 0), (652.9, 0, 0, 0, 0), (660.35, 0, 0, 0, 0)]

    return coillist


def evaluate_pipes(pipelist, coillist):
    pipecount = 0
    pipelength = 0
    pipelen = 0
    wholescraplength = 0
    wholescrapcount = 0
    scraplength = 0
    scrapcount = 0
    coillength = 0
    for coil in coillist:
        coillength += coil[0]
    print('coilength = ', coillength)
    print('\n')
    for pipes in pipelist:
        for pipe in pipes:
            pipelen = pipe[1] - pipe[2]
            if pipelen >= millvar.alt_Maximum_Length:
                scraplength += pipe[2]
                pipecount += 1
                pipelength += pipelen
            else:
                if pipelen >= millvar.alt_Minimum_Length:
                    scraplength += pipe[2]
                    pipecount += 1
                    pipelength += pipelen
                else:
                    if pipelen >= millvar.mill_Min_Length:
                        scraplength += pipe[2]
                        pipecount += 1
                        pipelength += pipelen
                    else:
                        wholescrapcount += 1
                        wholescraplength += pipe[1] + pipe[2]
                        scraplength += pipe[1] + pipe[2]
    if debugPrint:
        print(pipe[0], ',', round(pipe[1], 1), ',', round(pipe[2], 1))

    if debugPrint:
        print('total pipe length = ', round(pipelength, 2), coillength)
        print('scraplength = ', scraplength, 'whole scrap length= ', wholescraplength, ' scrap count = ',
              wholescrapcount)
        print('yield = ', round(pipelength / coillength, 2))
    return (coillength, round(pipelength, 2), pipecount, scraplength, wholescraplength, wholescrapcount,
            round(pipelength / coillength, 2))


# optimization
# This attempts to replicate the cut optimization logic as described in the functional spec
# and documented by the flowcharts.

def optimize(coil_DefectList, current_coil_length):
    # print('optimze defect list', coil_DefectList)
    coil_DefectList = clean_Defects(coil_DefectList)
    CAPL = 0.0
    NAPL = 0.0
    neg_tcount = 0
    if debugPrint:
        print("\n--Optimize--   current length = ", current_coil_length)
    # see previous cutlist for debugging purposes
    # print('cutlist before optimize', millvar.cutlist)

    # Clear cutlist
    cutlist = []
    if len(coil_DefectList) == 0:
        return []
        raise ValueError('zero length coilDefectList')

    steel_remain = get_ClosestDefect(coil_DefectList)

    defect_length = steel_remain.length
    defect_Type = steel_remain.defect_type
    available_steel = steel_remain.location

    next_Remain = get_Next_Closest_Defect(available_steel, coil_DefectList)
    next_defect_length = next_Remain.length
    next_defect_Type = next_Remain.defect_type
    next_available_steel = next_Remain.location
    if debugPrint:
        print('closest defect :', steel_remain.location, steel_remain.length)
        print('next defect :', next_Remain.location, next_defect_length)
    # footage = available_steel
    # print "Optimize ft=",available_steel,"defect =",defect_Type,"defect length=",defect_length
    fault_length = calc_total_fault_length(coil_DefectList)
    if debugPrint:
        print('length of closet fault = ', fault_length)

    # Problem
    # total_prime_steel = running_Coil_Length -fault_length

    # print('total prime = ',total_prime_steel)
    # print "total available prime steel = ",total_prime_steel

    #
    #  This would roughly correspond to PLC Main Algorithm #1
    #
    #
    #

    # Calculate Current Available Prime Length
    CAPL = available_steel  # - defect_length
    NAPL = next_available_steel  # - next_defect_length
    prime_steel = CAPL
    # How many max length pieces can we get from CAPL
    K_max_num_pieces = int(CAPL / millvar.max_Length)
    # do we subtract defect like flowchart or ignore it?
    # tail_Length = CAPL - (K_max_num_pieces*millvar.max_Length)
    #
    tail_Length = CAPL - (K_max_num_pieces * millvar.max_Length)  # - defect_length

    if debugPrint:
        print('CAPL: ', CAPL, ' K: ', K_max_num_pieces, 'tail: ', tail_Length, ' defect length: ', defect_length)
    ####### Add sanity check maybe?
    # if defect_length > tail_Length:
    # tail_Length=defect_length
    if tail_Length < 0:
        if debugPrint:
            print('tail < 0 : reducing K by 1')
        K_max_num_pieces -= 1
        tail_Length = CAPL - (K_max_num_pieces * millvar.max_Length) - defect_length

        if debugPrint:
            print('tail updated\nCAPL: ', CAPL, ' K: ', K_max_num_pieces, 'tail: ', tail_Length, ' defect length: ',
                  defect_length)
    if K_max_num_pieces > 0:
        if tail_Length >= millvar.alt_Minimum_Length:
            if debugPrint:
                print('tail > altmin')
            for i in range(0, int(K_max_num_pieces)):
                add_to_cutlist(cutlist, millvar.max_Length, 0)
                prime_steel -= millvar.max_Length
                # print('prime remaining:', prime_steel)
                # print ("-max length add to cutlist "+str(millvar.max_Length))

            #
            # if tail + defects etc > max length what do we do?  as specified this is a question
            # Brock does next line
            # add_to_cutlist(tail_Length+defect_length)
            leftover = tail_Length + defect_length
            if debugPrint:
                print('leftover = ', leftover)

            if leftover > millvar.mill_Max_Length:
                if debugPrint:
                    print("leftover Too big")
                return cutlist
            add_to_cutlist(cutlist, leftover, calc_scrap(defect_length, leftover))
            prime_steel -= leftover
            if debugPrint:
                print('prime remaining:', prime_steel)

        else:
            if debugPrint:
                print("Tail < alt_min ")
            P_max_len_pipes = int(
                math.ceil(millvar.alt_Minimum_Length - tail_Length) / (millvar.max_Length - millvar.alt_Minimum_Length))
            if debugPrint:
                print('P= ', P_max_len_pipes, 'K= ', K_max_num_pieces, 'Tail = ', tail_Length)

            if P_max_len_pipes > K_max_num_pieces:
                # P>K
                # Do the logic on PLC Short CAPL
                if debugPrint:
                    print(" P > K :Short CAPL")
                N_num_Alt_Min_Pipes = int(CAPL / millvar.alt_Minimum_Length)
                if debugPrint:
                    print('N = ', N_num_Alt_Min_Pipes)

                tail_Length2 = CAPL - (N_num_Alt_Min_Pipes * millvar.alt_Minimum_Length)
                if debugPrint:
                    print("tail 2=" + str(tail_Length2) + " defect = " + str(defect_length))

                if tail_Length2 >= millvar.mill_Min_Length:
                    # Cut N pipes wiith Alt_Min Length and last pipe with Tail2+Fault+Test
                    for i in range(0, N_num_Alt_Min_Pipes):
                        add_to_cutlist(cutlist, millvar.alt_Minimum_Length, 0)
                        prime_steel -= millvar.alt_Minimum_Length
                        # print('prime remaining:', prime_steel)

                    if tail_Length2 + defect_length <= millvar.mill_Max_Length:

                        add_to_cutlist(cutlist, tail_Length2 + defect_length,
                                       calc_scrap(defect_length, tail_Length2 + defect_length))

                        prime_steel -= tail_Length2 + defect_length
                        # print('prime remaining:', prime_steel)
                    else:
                        if debugPrint:
                            print('tail2 + defect > mill max length')
                        add_to_cutlist(cutlist, tail_Length2, calc_scrap(0, tail_Length2))
                        prime_steel -= tail_Length2
                        # print('prime remaining:', prime_steel)
                else:
                    if debugPrint:
                        print('tail2 < mill minimum')
                    # Add 1 pipe of max length then n-1 with alt minimum then attach tail 3 +defects to last alt min pipe
                    tail_Length3 = tail_Length2 + millvar.alt_Minimum_Length - millvar.max_Length
                    if debugPrint:
                        print('tail 3 = ', tail_Length3)

                    add_to_cutlist(cutlist, millvar.max_Length, 0)
                    prime_steel -= millvar.max_Length
                    # print('prime remaining:', prime_steel)
                    for i in range(0, N_num_Alt_Min_Pipes - 1):
                        add_to_cutlist(cutlist, millvar.alt_Minimum_Length, 0)
                        prime_steel -= millvar.alt_Minimum_Length
                        # print('prime remaining:', prime_steel)
                    if tail_Length3 >= 0:
                        add_to_cutlist(cutlist, tail_Length3 + defect_length,
                                       calc_scrap(defect_length, tail_Length3 + defect_length))
                        prime_steel -= tail_Length3 + defect_length
                    else:
                        if defect_length < millvar.mill_Min_Length:
                            add_to_cutlist(cutlist, millvar.mill_Min_Length,
                                           calc_scrap(defect_length, millvar.mill_Min_Length))
                        else:
                            add_to_cutlist(cutlist, defect_length, defect_length)
                            # print('prime remaining:', prime_steel)

            else:
                # P<=K
                if debugPrint:
                    print('P <=K ;P_max_len_pipes = ', P_max_len_pipes)
                if P_max_len_pipes > 0:
                    secondary_Length = round((tail_Length + (
                        P_max_len_pipes * millvar.max_Length) - millvar.alt_Minimum_Length) / P_max_len_pipes)
                    pass
                else:
                    if debugPrint:
                        print('set secondary to zero')
                    secondary_Length = 0

                    pass
                    if debugPrint:
                        print('secondary length = ', secondary_Length)
                if secondary_Length < millvar.mill_Min_Length:
                    secondary_Length = millvar.mill_Min_Length
                for i in range(0, K_max_num_pieces - P_max_len_pipes):
                    add_to_cutlist(cutlist, millvar.max_Length, 0)
                    prime_steel -= millvar.max_Length
                    if debugPrint:
                        print(' P<=K  ;add max length to cutlist', millvar.max_Length)
                        print('prime remaining:', prime_steel)
                        # print(" add max length pieces to cutlist  K-P-1=" + str(int(K_max_num_pieces - P_max_len_pipes) - 1))
                for i in range(0, P_max_len_pipes):
                    add_to_cutlist(cutlist, secondary_Length, 0)
                    prime_steel -= secondary_Length

                    if debugPrint:
                        print("add secondary to cutlist from PLC Page 2", secondary_Length)
                        print('prime remaining:', prime_steel)
                # if millvar.alt_Minimum_Length+defect_length <=millvar.mill_Max_Length:

                add_to_cutlist(cutlist, millvar.alt_Minimum_Length + defect_length,
                               calc_scrap(defect_length, millvar.alt_Minimum_Length + defect_length))
                if debugPrint:
                    print('add Alt minimum after secondary', millvar.alt_Minimum_Length + defect_length)

                    # add_to_cutlist(cutlist, millvar.alt_Minimum_Length + defect_length, defect_length)
                    # prime_steel -= millvar.alt_Minimum_Length + defect_length
                    # print('prime remaining:', prime_steel)
                    # else:
                    # add_to_cutlist(cutlist, millvar.alt_Minimum_Length , 0)
                    # prime_steel -= millvar.alt_Minimum_Length
                    # print('prime remaining:', prime_steel)
                    # Done with P<=K

    else:
        if debugPrint:
            print('K <=0')
        # tail_Length = CAPL + defect_length
        if tail_Length + defect_length < millvar.mill_Min_Length:

            if millvar.mill_Min_Length <= millvar.alt_Minimum_Length:
                add_to_cutlist(cutlist, millvar.mill_Min_Length, calc_scrap(defect_length, millvar.mill_Min_Length))
            else:
                add_to_cutlist(cutlist, millvar.mill_Min_Length, defect_length)
            prime_steel -= millvar.mill_Min_Length
            # print ('prime remaining:',prime_steel)
            # millvar.newfault = 0
            # return cutlist

        else:
            if tail_Length + defect_length > millvar.mill_Max_Length:
                add_to_cutlist(cutlist, tail_Length, 0)
                prime_steel -= tail_Length
                # print('prime remaining:', prime_steel)
                pass
            else:
                if tail_Length < millvar.alt_Minimum_Length:
                    add_to_cutlist(cutlist, tail_Length + defect_length,
                                   calc_scrap(defect_length, tail_Length + defect_length))
                else:
                    add_to_cutlist(cutlist, tail_Length + defect_length, defect_length)
                prime_steel -= tail_Length
                # print('prime remaining:', prime_steel)

            # millvar.newfault = 0
            # return cutlist
            add_front = CAPL
            # coil_DefectList = remove_defect(coil_DefectList, steel_remain)

    # print('final prime remaining:', prime_steel)
    return cutlist


def group_pipe(pipelist):
    line1_count = 0
    line2_count = 0
    line3_count = 0
    line4_count = 0
    line5_count = 0
    line1_length = 0
    line2_length = 0
    line3_length = 0
    line4_length = 0
    line5_length = 0
    line1_scrap = 0
    line2_scrap = 0
    line3_scrap = 0
    line4_scrap = 0
    line5_scrap = 0
    pipe0_count = 0
    pipe0_length = 0

    for pipe in pipelist:

        if pipe[1] - pipe[2] > millvar.alt_Maximum_Length:
            line1_count += 1
            line1_length += pipe[1] - pipe[2]
            line1_scrap += pipe[2]
        else:
            if pipe[1] - pipe[2] > millvar.alt_Minimum_Length:
                line2_count += 1
                line2_length += pipe[1] - pipe[2]
                line2_scrap += pipe[2]
            else:
                if pipe[1] - pipe[2] > millvar.mill_Min_Length:
                    line3_count += 1
                    line3_length += pipe[1] - pipe[2]
                    line3_scrap += pipe[2]
                else:
                    # all of this is scrap since the usable length < mill minimum
                    line4_count += 1
                    line4_length += pipe[1]
                    line4_scrap += pipe[1]
                    # for pipe in pipe0list:
                    #   if int(pipe[1]) > 0:
                    #       pipe0_count += 1
                    #       pipe0_length += pipe[1]

    pipegroup = millvar.PipeGroup(line1_count, line1_length, line1_scrap, line2_count, line2_length, line2_scrap,
                                  line3_count, line3_length, line3_scrap, line4_count, line4_length, line4_scrap)
    # ,pipe0_count, pipe0_length)
    return pipegroup


############################################################
#  run_1ft is called to simulate .1 foot of mill travel
#  there is a probablilty that there will be a mill stop
#  this is represented as # of stops per 10000 feet
#
# This updates the defect list to simulate 1 foot of mill movement
# pipe length and coil movement are handled elsewhere
#
#############################################################
def run_1ft(coil_DefectList):
    # print('run 1 ft ',coil_DefectList)
    # prepare for updated defect list
    newdefects = []
    nextCoilDefects = []
    millstop = 0

    # decrement defect footage counts and create new defect list
    for key in coil_DefectList:
        defect = coil_DefectList[key]
        dLoc = defect.location - millvar.simulation_step
        dLen = defect.length
        dType = defect.defect_type
        if dLoc > 0:
            newdefect = millvar.Defect(dLoc, dLen, dType)
            newdefects.append(newdefect)

    # Clear coil defect list before we rewrite it with updated information
    coil_DefectList.clear()
    # Rewrite defect list to reflect mill movement
    for defect in newdefects:
        defectid = defect.location
        if defectid > 0:
            coil_DefectList[defectid] = defect

    return coil_DefectList


def run_coil(coil, coil_num, headChop, millstop_carry):
    coil_pipelength = 0

    if debugPrint:
        print('Run coil ', coil, headChop)

    static_millStop = coil[4]  # Get sttic mill stop point
    if static_millStop == 0:
        static_millStop = -1000

    running_Coil_Length = coil[0] + headChop  # set the coil length and account for steel from previous coil
    coil_length = running_Coil_Length
    if debugPrint:
        print('start length = ', running_Coil_Length)
    tco_PipeLength = 0.0
    pipe_count = 0
    num_of_mill_stops = 0
    newpipes = []
    newfault = 0
    if debugPrint:
        print('load coil:', coil)
    coil_DefectList = load_Coil(coil, headChop)  # set initial defect list for the coil
    if debugPrint:
        print('preclean defects:', coil_DefectList)

    coil_DefectList = clean_Defects(coil_DefectList)  # clean up in case of negative from previous coil being removed
    if debugPrint:
        print(coil_DefectList, headChop)
    if millstop_carry > 0:
        coil_DefectList = add_defect(coil_DefectList, millstop_carry + headChop, millvar.millStop_BadLength, 3)
        if debugPrint:
            print(coil_DefectList)
        print('add millstop carry ', millstop_carry)
        if debugPrint:
            print('rc defects', coil_DefectList, millstop_carry)
    millstop_carry = 0
    # Do first pass at optimization and get first cut list
    if len(coil_DefectList) != 0:
        cutlist = optimize(coil_DefectList, running_Coil_Length)  # First Optimize the cuts
        if debugPrint:
            print('first cutlist\n', cutlist)
            print('defect list\n', coil_DefectList)

    # print('Initial cutlist   \n',cutlist)
    # print "fault length = ", fault_length


    pipe_number = 1

    # Run the coil until we run out
    if debugPrint:
        print('Running coil length: ', running_Coil_Length)
    while running_Coil_Length > millvar.mill_Min_Length:

        ##        if len(cutlist)== 0 or newfault == 1:
        ##            cutlist = optimize(coil_DefectList,running_Coil_Length)
        ##        thiscut = cutlist[0].length
        ##        thispipe= cutlist[0]
        for cut in cutlist:
            if debugPrint:
                print(cut)
            thiscut = cut[1]
            thisdefectlength = cut[2]
            if debugPrint:
                print('thiscut = ', thiscut)

            while tco_PipeLength <= thiscut:
                coil_DefectList = run_1ft(coil_DefectList)
                tco_PipeLength += millvar.simulation_step
                running_Coil_Length -= millvar.simulation_step
                # print(running_Coil_Length,tco_PipeLength)
                if running_Coil_Length - headChop >= static_millStop:
                    pass
                else:
                    # Add static mill stop if needed
                    if debugPrint:
                        print('*****Mill Stop*******', running_Coil_Length)
                    if running_Coil_Length > 153:
                        if debugPrint:
                            print('add mill stop defect')
                            print(coil_DefectList)
                        coil_DefectList = add_defect(coil_DefectList, 153, millvar.millStop_BadLength, 3)
                        if debugPrint:
                            print(coil_DefectList)
                        cutlist = []
                        newfault = 1
                    else:
                        millstop_carry = 153.0 - running_Coil_Length

                    static_millStop = -1000
                    if debugPrint:
                        print('first break')
                    break

            if newfault == 0:
                if debugPrint:
                    print('TCO Pipe = ', tco_PipeLength)
                    ### End While tco Pipelength < thiscut

                coil_pipe = '{0:0>4}'.format(str(coil_num)) + ' ' + '{0:0>2}'.format(str(pipe_number))
                cutpipe = (coil_pipe, thiscut, thisdefectlength)
                newpipes.append(cutpipe)
                pipe_number += 1
                coil_pipelength += thiscut
                if debugPrint:
                    print('add pipelength', tco_PipeLength, coil_pipelength)
                tco_PipeLength = 0
                if debugPrint:
                    print('--Running coil length: ', running_Coil_Length)

            else:
                if millstop_carry == 0:
                    if debugPrint:
                        print('mill stop re-optimize ')
                    cutlist = optimize(coil_DefectList, running_Coil_Length)
                else:
                    newfault = 0
            if newfault == 1:
                newfault = 0
                if debugPrint:
                    print('third break')
                break
        # if running_Coil_Length >= millvar.mill_Min_Length:
        if running_Coil_Length > millvar.mill_Min_Length:
            if debugPrint:
                print('re-optimize')
            cutlist = optimize(coil_DefectList, running_Coil_Length)



            ### End while running coil - finish and return
        if debugPrint:
            print(coil_pipelength, coil_length)
        headChop = round(coil_length - coil_pipelength, 2)
    if debugPrint:
        print('** headChop', headChop)

    coil_output = [headChop, newpipes, coil_DefectList, millstop_carry]
    if debugPrint:
        print('normal return', newpipes)
    return coil_output


def run_coil_list(coil_List):
    pipelist = []
    coil_num = 0
    headChop = 0
    dLoc = 0
    dLen = 0
    dType = 0
    millstop_carry = 0

    for coil in coil_List:
        coil_num += 1
        if debugPrint:
            print('coil=', coil)

        coil_DefectList = load_Coil(coil, headChop)

        coil_DefectList = add_defect(coil_DefectList, dLoc, dLen, dType)

        if debugPrint:
            print('**new coil defect list', coil_DefectList)

            # print ('updated defects',coil_DefectList)


            # --- Run a coil
            if debugPrint:
                print('coil loaded')
        result = run_coil(coil, coil_num, headChop, millstop_carry)
        if debugPrint:
            print('coil result\n', result)

        headChop = result[0]
        if debugPrint:
            print('headchop = ', headChop)
        coilpipes = result[1]

        # print('coilpipes',coilpipes)
        old_defect = result[2]
        if debugPrint:
            print('old defect\n\n')
        pipelist.append(coilpipes)
        millstop_carry = result[3]
        if debugPrint:
            print('*************mill stop carry ******', millstop_carry)

    for key in old_defect:
        defect = old_defect[key]
        dLoc = defect.location
        dLen = defect.length
        dType = defect.defect_type

    coil_DefectList = clean_Defects(coil_DefectList)

    if debugPrint:
        print('add ', headChop, ' to next coil')
        print('cd1', coil_DefectList)
    millvar.running_Coil_Length = 0

    return pipelist


def group_pipes(coilpipes):
    for coil in coilpipes:
        pipelen = 0
        pipecount = 0
        avglen = 0
        totalpipelen = 0
        line1count = 0
        line1totallength = 0
        line2count = 0
        line2totallength = 0
        line3count = 0
        line3totallength = 0
        line1avglen = 0
        line2avglen = 0
        line3avglen = 0
        wholescrapcount = 0
        wholescraplen = 0
        scraplen = 0
        for pipes in coil:
            for pipe in pipes:
                # print (pipe)
                pipelen = pipe[1] - pipe[2]
                # print(pipelen,pipecount)

                # print(totalpipelen)
                if pipelen >= millvar.alt_Maximum_Length:
                    line1count += 1
                    line1totallength += pipelen
                    scraplen += pipe[2]
                    pipecount += 1
                    totalpipelen += pipelen
                else:
                    if pipelen >= millvar.alt_Minimum_Length:
                        line2count += 1
                        line2totallength += pipelen
                        scraplen += pipe[2]
                        pipecount += 1
                        totalpipelen += pipelen
                    else:
                        if pipelen >= millvar.mill_Min_Length:
                            line3count += 1
                            line3totallength += pipelen
                            scraplen += pipe[2]
                            pipecount += 1
                            totalpipelen += pipelen
                        else:
                            wholescrapcount += 1
                            wholescraplen += pipe[1] + pipe[2]
                            scraplen += pipe[1] + pipe[2]
    if line1count > 0:
        line1avglen = round(line1totallength / line1count, 1)
    if line2count > 0:
        line2avglen = round(line2totallength / line2count, 1)
    if line3count > 0:
        line3avglen = round(line3totallength / line3count, 1)

    avglen = totalpipelen / pipecount

    print('average length: ,', avglen, ',scrap length: ,', round(scraplen, 1))
    print('Line 1 average length: ,', line1avglen, ',Line 1 count,', line1count, '\nLine 2 average length:,',
          line2avglen,
          'Line 2 count', line2count,
          '\nLine 3 average length:', line3avglen, 'Line 3 count', line3count,
          '\nwhole scrap length: ', wholescraplen, 'whole pipe scrap count: ', wholescrapcount)
    # print(pipes)
    pass


def main():
    millvar.max_Length = 80  # 63.7
    millvar.crossweld_BadLength = 10.0
    millvar.alt_Maximum_Length = 62.0  # 48.0
    millvar.alt_Minimum_Length = 42.0
    millvar.millStop_BadLength = 40.0
    millvar.mill_Max_Length = 83.0
    millvar.mill_Min_Length = 30.0
    millvar.millStop_Frequency = 15
    millvar.tco_ClampEngageLength = 5
    millvar.tear_BadLength = 5
    millvar.total_CoilLength = 0.0
    millvar.total_PipeLength = 0.0
    millvar.nextbad = []
    # initialize pipe length
    millvar.tco_PipeLength = 0
    headChop = 0

    coils_per_run = 1
    # set to indicate how many simulated runs for a given mill stop frequency
    runs_per_frequency = 10

    # set min and max frequency of mill stops per 10000 feet
    min_stop_frequency = 10
    max_stop_frequency = 20

    coilpipes = []
    millvar.running_Coil_Length = 0
    coil_DefectList = []
    # create sample coil lineup
    coil_List = create_simulation_coil_list(1, 30)
    print(coil_List)
    total_coilLength = 0
    starttime = time.strftime("%H:%M:%S")
    print('Begin simulation ', starttime)
    print('millvar.tear_BadLength:', millvar.tear_BadLength, ' millvar.millStop_BadLength: ',
          millvar.millStop_BadLength, 'millvar.crossweld_BadLength', millvar.crossweld_BadLength)

    for millvar.max_Length in [80, 62]:
        for millvar.alt_Maximum_Length in [62, 48]:
            for millvar.alt_Minimum_Length in [31, 40]:

                resultlist = []
                coilpipes = []

                pipecount = 0
                pipelength = 0.0
                coillength = 0.0
                wholescraplength = 0.0
                wholescrapcount = 0
                scraplength = 0.0
                scrapcount = 0
                for coil in coil_List:
                    coillength += coil[0]

                runpipes = run_coil_list(coil_List)
                pipelength = 0
                coilpipes.append(runpipes)
                for pipes in runpipes:
                    for pipe in pipes:
                        #print(pipe[0],',',pipe[1],',',pipe[2])
                        pass
                print('Max Length =  ', millvar.max_Length, ' alt max length = ', millvar.alt_Maximum_Length,
                      ' alt min length = ', millvar.alt_Minimum_Length, ' simulation_step= ', millvar.simulation_step)
                resultlist.append(evaluate_pipes(runpipes, coil_List))

                for result in resultlist:
                    print(result)
                group_pipes(coilpipes)

                pass
    print(coil_List)


main()



