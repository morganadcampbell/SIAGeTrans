import traci.constants as tc
import traci
import time
import sumolib
from controllers.bargainSolver import BargainSolver

###########################################
######## Adaptation Parameters ############
RunAdaptation = True                    ###
MinimumTime = 10                        ###
MaximumTime = 70                        ###
CurrentTemperature = 10                 ###
MaxTemperature = 30                     ###
MinTemperature = 10                     ###
EmergencyVehiclePriorization = 2        ###
FloodingPriorization = 2                ###
WeatherPriorization = 2                 ###
MaximumVehicleSpeed = 13.89  #(50km/h)  ### 
floodedVehicleSpeed = 4.17   #(15km/h)  ### 
###########################################
###########################################


###########################################################################################
######## General Info #####################################################################
numberOfPhases = 3                                                                      ###
edges = ['E1','E2','E3','E4']                                                           ###
crosswalk = [':J4_c0', ':J4_c1', ':J4_c2', ':J4_c3']                                    ###
entrySensors = ['e2_r1_in_1', 'e2_r1_in_2', 'e2_r2_in_1', 'e2_r2_in_2',                 ###
                'e2_r3_in_1', 'e2_r3_in_2', 'e2_r4_in_1', 'e2_r4_in_2']                 ###
exitSensors = ['e2_r1_out_1', 'e2_r1_out_2', 'e2_r2_out_1', 'e2_r2_out_2',              ###
               'e2_r3_out_1', 'e2_r3_out_2', 'e2_r4_out_1', 'e2_r4_out_2']              ###
###########################################################################################
######## Phase Info #######################################################################
entrySensorsPerPhase = [['e2_r4_in_2', 'e2_r2_in_2'], ['e2_r1_in_2', 'e2_r3_in_2'],     ###
                        ['e2_r1_in_1', 'e2_r2_in_1', 'e2_r3_in_1', 'e2_r4_in_1']]     	###
exitSensorsPerPhase = [['e2_r4_out_1', 'e2_r2_out_2'], ['e2_r1_out_2', 'e2_r3_out_2'],  ###
                       ['e2_r1_out_1', 'e2_r2_out_1'], ['e2_r3_out_1', 'e2_r4_out_2']]  ###
lanePerPhase = [['E2_2', 'E4_2'],['E1_2', 'E3_2'],['E1_1', 'E2_1', 'E3_1', 'E4_1']]     ###
closedLanes = ['E1_1']                                                                  ###
floodedLanes = ['E1_2']                                                                 ###
crosswalkPerPhase = [[':J4_c1', ':J4_c3'], [':J4_c0', ':J4_c2'],[]]                     ###
PeopleEdgePerPhase = [['E2', 'E4'], ['E1', 'E3'],[]]                                    ###
###########################################################################################
###########################################################################################


def runAdaptation(passingVehicles, queuedVehiclesLane, laneClosure, floodedVehiclesLane, queuedVIPVehiclesLane, passingPeople, queuedPeopleEdge) -> []:
    fixedParams = dict()
    fixedParams["phases"] = numberOfPhases # number of cycle's phases
    fixedParams["minimumTime"] = MinimumTime # minimum accepted time for a phase
    fixedParams["maximumTime"] = MaximumTime # maximum accepted time for a phase
    fixedParams["waitingTime"] = 5 # waiting time between phases (default = 1s)
    fixedParams["d"] = [MinimumTime, MinimumTime, MinimumTime] # desagreement value for each phase (default = minimumTime)
    fixedParams["w"] = 1.34 # persons per car
    fixedParams["Tcur"] = CurrentTemperature # current temperature
    fixedParams["Tmax"] = MaxTemperature # max teperature
    fixedParams["Tmin"] = MinTemperature # min temperature
    fixedParams["Pvip"] = EmergencyVehiclePriorization # priority vehicles priorization factor
    fixedParams["Pfld"] = FloodingPriorization # flooding priorization factor
    fixedParams["Pwea"] = WeatherPriorization # weather priorization factor
    fixedParams["t_c"] = 105 # cycle's total time (sum of green time + waiting time (5s) for each phase)

    phaseParams = []
    for p in range(numberOfPhases):
        params = dict()
        params["PDT_j"] = [y for x,y in queuedPeopleEdge.items() if x in PeopleEdgePerPhase[p]] # queued pedestrian in sidewalk (j) of a phase (i)
        params["INDcls_l"] = [y for x,y in laneClosure.items() if x in lanePerPhase[p]] # index of closure for a roadsection (l) in a phase (i)
        params["VCL_l"] = [y for x,y in queuedVehiclesLane.items() if x in lanePerPhase[p]] # queued vehicles per roadsection (l) in a phase (i)
        params["DeltaVCLin_l"] = [y/100 for x,y in passingVehicles.items() if x in entrySensorsPerPhase[p]] # roadsection (l) arriving vehicles rate (per second) in a phase (i)
        params["DeltaPDTin_j"] = [y/100 for x,y in passingPeople.items() if x in PeopleEdgePerPhase[p]] # sideway (j) arriving pedestrian rate (per second) in a phase (i)
        params["DeltaVCLout_l"] = [y/100 for x,y in passingVehicles.items() if x in exitSensorsPerPhase[p]] # roadsection (l) departing vehicles rate (per second) in a phase (i)
        params["DeltaPDTout_j"] = [y/100 for x,y in passingPeople.items() if x in crosswalkPerPhase[p]] # sideway (j) departing pedestrian rate (per second) in a phase (i)
        params["VCLvip_i"] = sum([y for x,y in queuedVIPVehiclesLane.items() if x in lanePerPhase[p]]) # number of prioritary vehicles in a phase (i)
        params["VCLfld_i"] = sum([y for x,y in floodedVehiclesLane.items() if x in lanePerPhase[p]])  # number of vehicles in a flooding in a phase (i)
        params["VCLvip_tot"] = sum(queuedVIPVehiclesLane.values()) # total number of prioritary vehicles in the intersection
        params["VCLfld_tot"] = sum(floodedVehiclesLane.values()) # total number of vehicles in a flooding in the intersection
        phaseParams.append(params)

    bestx = BargainSolver.getBestSetup(fixedParams,phaseParams)

    program = traci.trafficlight.getCompleteRedYellowGreenDefinition('J4')[0]
    for i in range(len(bestx)):
        program.phases[i*2].duration = bestx[i]
    traci.trafficlight.setProgramLogic('J4', program)
    return bestx


def runSimulation():
    traci.start(sumoCmd) #starting simulation
    passingVehicles = dict()
    queuedVehiclesLane = dict()
    laneClosure = dict()
    floodedVehiclesLane = dict()
    queuedVIPVehiclesLane = dict()
    passingPeople = dict()
    queuedPeopleEdge = dict()
    step = 0

    #subscribing to collect data
    traci.edge.subscribeContext(edges[0], tc.CMD_GET_EDGE_VARIABLE, 600, [tc.LAST_STEP_VEHICLE_NUMBER, tc.LAST_STEP_PERSON_ID_LIST])
    traci.lane.subscribeContext('E1_1', tc.CMD_GET_LANE_VARIABLE, 600, [tc.LAST_STEP_VEHICLE_NUMBER, tc.LAST_STEP_VEHICLE_ID_LIST])
    traci.lanearea.subscribeContext(entrySensors[0], tc.CMD_GET_LANEAREA_VARIABLE, 600, [tc.VAR_LAST_INTERVAL_NUMBER])

    #setting up closed lanes
    for lane in closedLanes:
        traci.lane.setDisallowed(lane, ['all'])

    #setting up flooded lanes
    for lane in sum(lanePerPhase, []):
        if lane in floodedLanes:
            traci.lane.setMaxSpeed(lane, floodedVehicleSpeed)
        else:
            traci.lane.setMaxSpeed(lane, MaximumVehicleSpeed)

    # simulation loop
    while traci.simulation.getMinExpectedNumber() > 0:

        # collecting data from people
        for x,y in traci.edge.getContextSubscriptionResults(edges[0]).items(): 
            if x in crosswalk + edges:
                passingPeople[x] = passingPeople.get(x, set()).union(set(y[tc.LAST_STEP_PERSON_ID_LIST]))

        if (step - 1) % 1000 == 0: # test for adaptation

            # parsing data from people
            passingPeople = {x : len(y) for x,y in passingPeople.items()}
            # collecting data from queued people
            for x,y in traci.edge.getContextSubscriptionResults(edges[0]).items(): 
                if x in edges:
                    queuedPeopleEdge[x] = queuedPeopleEdge.get(x, 0) + len(y[tc.LAST_STEP_PERSON_ID_LIST])

            # collecting queueing metrics
            for x,y in traci.lane.getContextSubscriptionResults('E1_1').items(): 
                if x[0:2] in edges: 
                    queuedVehiclesLane[x] = queuedVehiclesLane.get(x, 0) + y[tc.LAST_STEP_VEHICLE_NUMBER]
                    queuedVIPVehiclesLane[x] = sum([1 for v in y[tc.LAST_STEP_VEHICLE_ID_LIST] if traci.vehicle.getTypeID(v) == 'VIP'])
                    laneClosure[x] = laneClosure.get(x, 1 if x in closedLanes else 0)
                    floodedVehiclesLane[x] = floodedVehiclesLane.get(x, 0) + (y[tc.LAST_STEP_VEHICLE_NUMBER] if x in floodedLanes else 0)


            # collecting arriving and departing metrics
            for x,y in traci.lanearea.getContextSubscriptionResults(entrySensors[0]).items(): 
                passingVehicles[x] = passingVehicles.get(x, 0) + y[tc.VAR_LAST_INTERVAL_NUMBER]

            # running adaptation on traffic light
            if RunAdaptation: runAdaptation(passingVehicles, queuedVehiclesLane, laneClosure, floodedVehiclesLane, queuedVIPVehiclesLane, passingPeople, queuedPeopleEdge)

            # reset metrics
            passingVehicles.clear()
            queuedVehiclesLane.clear()
            laneClosure.clear()
            floodedVehiclesLane.clear()
            queuedVIPVehiclesLane.clear()
            passingPeople.clear()
            queuedPeopleEdge.clear()

        # time.sleep(0.005) # pacing the simulation
        traci.simulationStep()
        step += 1

    traci.close() #stoping simulation


if __name__ == "__main__":
    sumo_binary = sumolib.checkBinary('sumo-gui') # or 'sumo-gui'
    sumoCmd = [sumo_binary, "-c", "sumo_simulation/sumo_elements/Exemplo/teste.sumocfg", "--duration-log.statistics", "--log", "sumo_simulation/metrics/logfile.txt"]
    runSimulation()
