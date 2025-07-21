import traci.constants as tc
import traci
import math

from controllers.bargainSolver import BargainSolver

###########################################################################################
##### Fixed Parameters (Informative) ######################################################
########### !CANNOT BE CHANGED! ###########################################################
defaultVehicleFlowProbability = 0.04                                                    ###
emrgVehicleFlowProbability = 0.001                                                      ###
pedestrianFlowProbability = 0.04                                                        ###
simulationDuration = 10000 # !!must be equal to vehicle flow duration!!                 ###
adaptationInterval = 600 #10min - !!must be equal to LaneArea Detectors period!!        ###
numberOfPhases = 3                                                                      ###
fixedPhaseTime = 30      # (seconds)                                                    ###
waitingTime = 5          # (seconds)                                                    ###
cicleFullTime = 105      # (seconds)                                                    ###
trafficLightTimes = []   # values will be added during simulation                       ###
lanesWithEmrgVehicle = {} # values will be added during simulation                      ###
###########################################################################################
edges = ['E1','E2','E3','E4']                                                           ###
crosswalk = [':J4_c0', ':J4_c1', ':J4_c2', ':J4_c3']                                    ###
entrySensors = ['e2_r1_in_1', 'e2_r1_in_2', 'e2_r2_in_1', 'e2_r2_in_2',                 ###
                'e2_r3_in_1', 'e2_r3_in_2', 'e2_r4_in_1', 'e2_r4_in_2']                 ###
exitSensors = ['e2_r1_out_1', 'e2_r1_out_2', 'e2_r2_out_1', 'e2_r2_out_2',              ###
               'e2_r3_out_1', 'e2_r3_out_2', 'e2_r4_out_1', 'e2_r4_out_2']              ###
entrySensorsPerPhase = [['e2_r4_in_2', 'e2_r2_in_2'], ['e2_r1_in_2', 'e2_r3_in_2'],     ###
                        ['e2_r1_in_1', 'e2_r2_in_1', 'e2_r3_in_1', 'e2_r4_in_1']]     	###
exitSensorsPerPhase = [['e2_r4_out_1', 'e2_r2_out_2'], ['e2_r1_out_2', 'e2_r3_out_2'],  ###
                       ['e2_r1_out_1', 'e2_r2_out_1'], ['e2_r3_out_1', 'e2_r4_out_2']]  ###
lanePerPhase = [['E2_2', 'E4_2'],['E1_2', 'E3_2'],['E1_1', 'E2_1', 'E3_1', 'E4_1']]     ###
crosswalkPerPhase = [[':J4_c1', ':J4_c3'], [':J4_c0', ':J4_c2'],[]]                     ###
PeopleEdgePerPhase = [['E2', 'E4'], ['E1', 'E3'],[]]                                    ###
###########################################################################################
###########################################################################################


def RunAdaptation(simulationParams, passingVehicles, queuedVehicles, floodedVehicles, queuedEmrgVehicles, passingPeople, queuedPeople) -> []:
    fixedParams = dict()
    fixedParams["phases"] = numberOfPhases # number of cycle's phases
    fixedParams["minimumTime"] = simulationParams.get('MinimumTime') # minimum accepted time for a phase
    fixedParams["maximumTime"] = simulationParams.get('MaximumTime') # maximum accepted time for a phase
    fixedParams["waitingTime"] = waitingTime # waiting time between phases (default = 1s)
    fixedParams["dParams"] = [simulationParams.get('MinimumTime'), simulationParams.get('MinimumTime'), simulationParams.get('MinimumTime')] # parameters for calculate desagreement value for each phase (default = params.get('MinimumTime'])
    fixedParams["w"] = simulationParams.get('personPerCarFactor') # persons per car
    fixedParams["Tcur"] = simulationParams.get('CurrentTemperature') # current temperature
    fixedParams["Tmax"] = simulationParams.get('MaxTemperature') # max teperature
    fixedParams["Tmin"] = simulationParams.get('MinTemperature') # min temperature
    fixedParams["Pemrg"] = simulationParams.get('EmergencyVehiclePriorization') # priority vehicles priorization factor
    fixedParams["Pfld"] = simulationParams.get('FloodingPriorization') # flooding priorization factor
    fixedParams["Pwea"] = simulationParams.get('WeatherPriorization') # weather priorization factor
    fixedParams["t_c"] = cicleFullTime # cycle's total time (sum of green time + waiting time (5s) for each phase)
    fixedParams["DVFp"] = defaultVehicleFlowProbability # probability for emitting a default vehicle each second in each route
    fixedParams["VVFp"] = emrgVehicleFlowProbability # probability for emitting a Emrg vehicle each second in each route
    fixedParams["PFp"] = pedestrianFlowProbability # probability for emitting a pedestrian each second in each route
    phaseParams = []
    for p in range(numberOfPhases):
        params = dict()
        params["PDT_j"] = [y for x,y in queuedPeople.items() if x in PeopleEdgePerPhase[p]] # queued pedestrian in sidewalk (j) of a phase (i)
        params["VCL_l"] = [y for x,y in queuedVehicles.items() if x in lanePerPhase[p]] # queued vehicles per roadsection (l) in a phase (i)
        params["DeltaVCLin_l"] = [y/adaptationInterval for x,y in passingVehicles.items() if x in entrySensorsPerPhase[p]] # roadsection (l) arriving vehicles rate (per second) in a phase (i)
        params["DeltaPDTin_j"] = [y/adaptationInterval for x,y in passingPeople.items() if x in PeopleEdgePerPhase[p]] # sideway (j) arriving pedestrian rate (per second) in a phase (i)
        params["DeltaVCLout_l"] = [y/adaptationInterval for x,y in passingVehicles.items() if x in exitSensorsPerPhase[p]] # roadsection (l) departing vehicles rate (per second) in a phase (i)
        params["DeltaPDTout_j"] = [y/adaptationInterval for x,y in passingPeople.items() if x in crosswalkPerPhase[p]] # sideway (j) departing pedestrian rate (per second) in a phase (i)
        params["VCLemrg_i"] = sum([y for x,y in queuedEmrgVehicles.items() if x in lanePerPhase[p]]) # number of prioritary vehicles in a phase (i)
        params["VCLfld_i"] = sum([y for x,y in floodedVehicles.items() if x in lanePerPhase[p]])  # number of vehicles in a flooding in a phase (i)
        params["VCLemrg_tot"] = sum(queuedEmrgVehicles.values()) # total number of prioritary vehicles in the intersection
        params["VCLfld_tot"] = sum(floodedVehicles.values()) # total number of vehicles in a flooding in the intersection
        phaseParams.append(params)

    #calculating bias (to prioritize emergency vehicles)
    EmrgsPerPhase = [x.get('VCLemrg_i') for x in phaseParams]
    remainingTime = cicleFullTime - (simulationParams.get('MinimumTime') * EmrgsPerPhase.count(0)) - (waitingTime * numberOfPhases)
    totalEmrgVehicles = sum(EmrgsPerPhase)
    EmrgsPerPhaseIndexed = {i : EmrgsPerPhase[i] for i in range(len(EmrgsPerPhase)) if EmrgsPerPhase[i] != 0}
    if simulationParams.get('EmergencyVehiclePriorization'):
        bias = {k : min(math.floor(v * remainingTime / totalEmrgVehicles), simulationParams.get('MaximumTime'))  for k,v in EmrgsPerPhaseIndexed.items()}
    else: bias = dict()

    bestx = BargainSolver.getBestSetup(fixedParams,phaseParams,bias)
    trafficLightTimes.append(bestx)
    program = traci.trafficlight.getCompleteRedYellowGreenDefinition('J4')[0]
    for i in range(len(bestx)):
        program.phases[i*3].duration = bestx[i]
    traci.trafficlight.setProgramLogic('J4', program)
    return bestx


def runSimulation(sumoCmd : str, simulationParams : dict):
    traci.start(sumoCmd) #starting simulation
    passingVehicles = dict();queuedVehicles = dict();floodedVehicles = dict();queuedEmrgVehicles = dict();passingPeople = dict();queuedPeople = dict()
    LastPassingVehicles = dict();LastQueuedVehicles = dict();LastFloodedVehicles = dict();LastPassingPeople = dict();LastQueuedPeople = dict()
    step = 0

    #subscribing to collect data
    traci.edge.subscribeContext(edges[0], tc.CMD_GET_EDGE_VARIABLE, 600, [tc.LAST_STEP_VEHICLE_NUMBER, tc.LAST_STEP_PERSON_ID_LIST])
    traci.lane.subscribeContext('E1_1', tc.CMD_GET_LANE_VARIABLE, 600, [tc.LAST_STEP_VEHICLE_NUMBER, tc.LAST_STEP_VEHICLE_ID_LIST])
    traci.lanearea.subscribeContext(entrySensors[0], tc.CMD_GET_LANEAREA_VARIABLE, 600, [tc.VAR_LAST_INTERVAL_NUMBER])

    #setting up flooded lanes
    for lane in sum(lanePerPhase, []):
        if lane in simulationParams.get('floodedLanes'):
            traci.lane.setMaxSpeed(lane, simulationParams.get('floodedVehicleSpeed'))
        else:
            traci.lane.setMaxSpeed(lane, simulationParams.get('MaximumVehicleSpeed'))

    # simulation loop
    while traci.simulation.getMinExpectedNumber() > 0:

        #to unbalance traffic, add vehicles to r_0 and r_4 (right-to-left and left-to-right)
        if simulationParams.get('trafficImbalanceFactor') > 0 and step < simulationDuration and step % simulationParams.get('trafficImbalanceFrequency') == 0:
            for i in range(simulationParams.get('trafficImbalanceFactor')): traci.vehicle.add(f'ins{step}_r0_{i}', 'r_0')
            for i in range(simulationParams.get('trafficImbalanceFactor')): traci.vehicle.add(f'ins{step}_r4_{i}', 'r_4')

        # collecting data from people
        for x,y in traci.edge.getContextSubscriptionResults(edges[0]).items(): 
            if x in crosswalk + edges:
                passingPeople[x] = passingPeople.get(x, set()).union(set(y[tc.LAST_STEP_PERSON_ID_LIST]))

        # test adaptation to prioritize emergency vehicle
        if simulationParams.get('RunAdaptation') and simulationParams.get('EmrgVhcAdaptationInterval') and step % simulationParams.get('EmrgVhcAdaptationInterval') == 0:
            for x,y in traci.lane.getContextSubscriptionResults('E1_1').items(): 
                if x[0:2] in edges: 
                    queuedEmrgVehicles[x] = sum([1 for v in y[tc.LAST_STEP_VEHICLE_ID_LIST] if traci.vehicle.getTypeID(v) == 'VIP'])
            if sum(list(queuedEmrgVehicles.values())) > 0: #if there is emergency vehicles, adapt
                RunAdaptation(simulationParams, LastPassingVehicles, LastQueuedVehicles, LastFloodedVehicles, queuedEmrgVehicles, LastPassingPeople, LastQueuedPeople)


        if simulationParams.get('RunAdaptation') and step > 0 and step % adaptationInterval == 0: # test for adaptation

            # parsing data from people
            passingPeople = {x : len(y) for x,y in passingPeople.items()}
            # collecting data from queued people
            for x,y in traci.edge.getContextSubscriptionResults(edges[0]).items(): 
                if x in edges:
                    queuedPeople[x] = queuedPeople.get(x, 0) + len(y[tc.LAST_STEP_PERSON_ID_LIST])

            # collecting vehicle queueing metrics
            for x,y in traci.lane.getContextSubscriptionResults('E1_1').items(): 
                if x[0:2] in edges: 
                    queuedVehicles[x] = queuedVehicles.get(x, 0) + y[tc.LAST_STEP_VEHICLE_NUMBER]
                    queuedEmrgVehicles[x] = sum([1 for v in y[tc.LAST_STEP_VEHICLE_ID_LIST] if traci.vehicle.getTypeID(v) == 'VIP'])
                    floodedVehicles[x] = floodedVehicles.get(x, 0) + (y[tc.LAST_STEP_VEHICLE_NUMBER] if x in simulationParams.get('floodedLanes') else 0)

            # collecting arriving and departing metrics
            for x,y in traci.lanearea.getContextSubscriptionResults(entrySensors[0]).items(): 
                passingVehicles[x] = passingVehicles.get(x, 0) + y[tc.VAR_LAST_INTERVAL_NUMBER]

            # running adaptation on traffic light
            RunAdaptation(simulationParams, passingVehicles, queuedVehicles, floodedVehicles, queuedEmrgVehicles, passingPeople, queuedPeople)

            # reset metrics
            LastPassingVehicles = passingVehicles.copy();LastQueuedVehicles = queuedVehicles.copy();LastFloodedVehicles = floodedVehicles.copy();LastPassingPeople = passingPeople.copy();LastQueuedPeople = queuedPeople.copy()
            passingVehicles.clear();queuedVehicles.clear();floodedVehicles.clear();queuedEmrgVehicles.clear();passingPeople.clear();queuedPeople.clear()

        # time.sleep(0.005) # pacing the simulation
        traci.simulationStep()
        step += 1

    traci.close() #stoping simulation
