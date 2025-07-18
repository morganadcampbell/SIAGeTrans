from sumo_simulation.auxiliar.sumoController import *
from sumo_simulation.auxiliar.parsingLogFile import *
import os
import io
import sys
import json
import datetime
import sumolib

##############################################
######## Adaptation Parameters ###############
simulationParams = {                       ###
'RunAdaptation' : True,                    ###
'MinimumTime' : 15,                        ###
'MaximumTime' : 45,                        ###
'CurrentTemperature' : 20,                 ###
'MaxTemperature' : 30,                     ###
'MinTemperature' : 10,                     ###
'EmergencyVehiclePriorization' : 0,        ### 0 False; 1 True
'EmrgVhcAdaptationInterval' : 10,          ###
'FloodingPriorization' : 0,                ###
'WeatherPriorization' : 1,                 ###
'personPerCarFactor' : 1.54,               ###
'trafficImbalanceFactor' : 0,              ### How many vehicles will be added in each iteration (set 0 for balanced traffic)
'trafficImbalanceFrequency' : 20,          ### How many steps between each iteration of inserting vehicles (unbalanced traffic distribution)
'MaximumVehicleSpeed' : 16.67,  #(60km/h)  ### Regular vehicle speed
'floodedVehicleSpeed' : 4.17,   #(15km/h)  ### 
'floodedLanes' : ['E1_2', 'E1_1', 'E3_2']  ###
}                                          ###
##############################################
##############################################

def simulation(test = [simulationParams] ):
    for i in range(len(test)):
        print(f'\n **** Running test {i+1}/{len(tests)} ****\n\n')
        t = test[i]
        #setting simulation simulationParams
        sumo_binary = sumolib.checkBinary('sumo') # or 'sumo-gui' for GUI
        currentDatetime = datetime.datetime.now()
        logfileComplement = currentDatetime.strftime("%Y%m%d_%H%M%S_") + ('fixed' if not t.get('RunAdaptation') else 'adaptive')
        sumoCmd = [sumo_binary, "-c", "sumo_simulation/sumo_elements/test.sumocfg", 
                    "--duration-log.statistics", 
                    "--tripinfo-output", "sumo_simulation/sumo_elements/metrics/" + logfileComplement + "_tripinfo_log.xml", "--device.emissions.probability", "1.0",
                    "--log", "sumo_simulation/sumo_elements/metrics/" + logfileComplement + "_metrics.log"]

        ## start simulation
        runSimulation(sumoCmd, t)

        #renaming log file
        os.rename("sumo_simulation/sumo_elements/metrics/lanedata.xml", "sumo_simulation/sumo_elements/metrics/" + logfileComplement + "_lanedata.xml")

        #parsing logfiles
        insertedVehicles,vehicleDuration,vehicleTimeLoss,insertedPedestrian,pedestrianDuration,pedestrianTimeLoss = getWeightedMetrics("sumo_simulation/sumo_elements/metrics/" + logfileComplement + "_metrics.log") #getting metrics
        timeLossMap,waitingTimeMap,floodedWaitingTimeMap,totalWaitingTime,totalFloodedWaitingTime,adjustedFloodedWaitingTime,floodedTimeLossMap,totalTimeLoss,totalFloodedTimeLoss,adjustedFloodedTimeLoss = getWeightedLaneMetrics("sumo_simulation/sumo_elements/metrics/" + logfileComplement + "_lanedata.xml", t.get('floodedLanes')) #getting metrics
        CO2EmissionAvg,fuelUseAvg,EmrgWaitingTimeAvg,EmrgTimeLossAvg,EmrgDurationAvg,vehicleWaitingTimeAvg = getEmissionAndEmrgMetrics("sumo_simulation/sumo_elements/metrics/" + logfileComplement + "_tripinfo_log.xml") #getting metrics

        #calculating metrics
        WeightedTimeLoss = ((insertedVehicles * vehicleTimeLoss) + (insertedPedestrian * pedestrianTimeLoss)) / (insertedVehicles + insertedPedestrian)
        WeightedDuration = ((insertedVehicles * vehicleDuration) + (insertedPedestrian * pedestrianDuration)) / (insertedVehicles + insertedPedestrian)

        #calculating weather info
        WeatherVariance = (t.get('CurrentTemperature') - ((t.get('MaxTemperature') + t.get('MinTemperature'))/2)) ** 2
        WeatherVariationFactor = abs(t.get('CurrentTemperature') - ((t.get('MaxTemperature') + t.get('MinTemperature'))/2) ) / ((t.get('MaxTemperature') - t.get('MinTemperature'))/2)

        #including simulation info to metrics.log
        with open("sumo_simulation/sumo_elements/metrics/" + logfileComplement + "_metrics.log", 'a') as file: 
            file.write("\n-----------------------------------------------------------\n**** Adding simulation parameters from Sumo Controller ****\n")
            file.write(f'{t.get('RunAdaptation')= }\n{t.get('MinimumTime')= }\n{t.get('MaximumTime')= }\n{t.get('CurrentTemperature')= }\n{t.get('MaxTemperature')= }\n{t.get('MinTemperature')= }\n{t.get('EmergencyVehiclePriorization')= }\n{t.get('FloodingPriorization')= }\n{t.get('WeatherPriorization')= }\
                        \n{t.get('personPerCarFactor')= }\n{t.get('MaximumVehicleSpeed')= }\n{t.get('floodedVehicleSpeed')= }\n{t.get('floodedLanes')= }\n{defaultVehicleFlowProbability= }\n{emrgVehicleFlowProbability= }\n{pedestrianFlowProbability= }\
                        \n{adaptationInterval= }\n{numberOfPhases= }\n{fixedPhaseTime= }\n{waitingTime= }\n{cicleFullTime= }\n{edges= }\n{crosswalk= }\n{entrySensors= }\n{exitSensors= }\n{entrySensorsPerPhase= }\n{exitSensorsPerPhase= }\
                        \n{lanePerPhase= }\n{crosswalkPerPhase= }\n{PeopleEdgePerPhase= }\n{trafficLightTimes= }\n{t.get('trafficImbalanceFrequency')= }\n{t.get('trafficImbalanceFactor')= }\
                        \n{WeightedTimeLoss= }\n{WeightedDuration= }\n{WeatherVariance= }\n{WeatherVariationFactor= }\
                        \n{timeLossMap= }\n{waitingTimeMap= }\n{floodedWaitingTimeMap= }\n{totalWaitingTime= }\n{totalFloodedWaitingTime= }\n{adjustedFloodedWaitingTime= }\
                        \n{floodedTimeLossMap= }\n{totalTimeLoss= }\n{totalFloodedTimeLoss= }\n{adjustedFloodedTimeLoss= }\
                        \n{CO2EmissionAvg= }\n{fuelUseAvg= }\n{EmrgWaitingTimeAvg= }\n{EmrgTimeLossAvg= }\n{EmrgDurationAvg= }')

        #inserting simulation data into simulation.log
        with open("sumo_simulation/simulation.log", 'a+') as file:
            file.write(f'**** Simulation Results from {currentDatetime.strftime("%d/%m/%Y at %H:%M:%S")} ****\n')
            file.write(f'**Comparative Metrics**\n\t{WeightedTimeLoss= }\n\t{WeightedDuration= }\n\t{adjustedFloodedWaitingTime= }\n\t{adjustedFloodedTimeLoss= }\n\t{CO2EmissionAvg= }\n\t{fuelUseAvg= }\n\t{EmrgWaitingTimeAvg= }\n\t{EmrgTimeLossAvg= }\n\t{EmrgDurationAvg= }\n\t{vehicleWaitingTimeAvg= }\n\n')
            file.write(f'**Simulation Parameters**\n\tRunAdaptation= {t.get('RunAdaptation')}\n\ttrafficImbalanceFactor= {t.get('trafficImbalanceFactor')}\n\ttrafficImbalanceFrequency= {t.get('trafficImbalanceFrequency')}\n\tEmergencyVehiclePriorization= {t.get('EmergencyVehiclePriorization')}\n\tFloodingPriorization= {t.get('FloodingPriorization')}\n\tWeatherPriorization= {t.get('WeatherPriorization')}\n\n')
            file.write(f'**Simulation Data**\n\t{WeatherVariance= }\n\t{WeatherVariationFactor= }\n\t{insertedVehicles= }\n\t{vehicleTimeLoss= }\n\t{insertedPedestrian= }\n\t{pedestrianTimeLoss= }\n\t{totalWaitingTime= }\n\t{totalFloodedWaitingTime= }\n\t{totalTimeLoss= }\n\t{totalFloodedTimeLoss= }\n\n')
            file.write('Full Metrics at: ' + "sumo_simulation/sumo_elements/metrics/" + logfileComplement + "_metrics.log\n")
            file.write('LaneArea Metrics at: ' + "sumo_simulation/sumo_elements/metrics/" + logfileComplement + "_lanedata.xml\n")
            file.write("--------------------------------------------------------\n")

        #inserting simulation data into simulation.csv
        with open("sumo_simulation/simulation.csv", 'a+') as file:
            file.seek(0) #writing header if needed
            if file.readline() == '': file.write(f'WeightedTimeLoss;WeightedDuration;adjustedFloodedWaitingTime;adjustedFloodedTimeLoss;CO2EmissionAvg;fuelUseAvg;EmrgWaitingTimeAvg;EmrgTimeLossAvg;EmrgDurationAvg;vehicleWaitingTimeAvg;RunAdaptation;trafficImbalanceFactor;trafficImbalanceFrequency;EmergencyVehiclePriorization;FloodingPriorization;WeatherPriorization;WeatherVariance;WeatherVariationFactor;insertedVehicles;vehicleTimeLoss;insertedPedestrian;pedestrianTimeLoss;totalWaitingTime;totalFloodedWaitingTime;totalTimeLoss;totalFloodedTimeLoss\n')
            file.seek(io.SEEK_END) #appending data to the file
            file.write(f'{WeightedTimeLoss};{WeightedDuration};{adjustedFloodedWaitingTime};{adjustedFloodedTimeLoss};{CO2EmissionAvg};{fuelUseAvg};{EmrgWaitingTimeAvg};{EmrgTimeLossAvg};{EmrgDurationAvg};{vehicleWaitingTimeAvg};{t.get('RunAdaptation')};{t.get('trafficImbalanceFactor')};{t.get('trafficImbalanceFrequency')};{t.get('EmergencyVehiclePriorization')};{t.get('FloodingPriorization')};{t.get('WeatherPriorization')};{WeatherVariance};{WeatherVariationFactor};{insertedVehicles};{vehicleTimeLoss};{insertedPedestrian};{pedestrianTimeLoss};{totalWaitingTime};{totalFloodedWaitingTime};{totalTimeLoss};{totalFloodedTimeLoss}\n')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        print(sys.argv)
        try:
            filename = sys.argv[1]
            with open(filename, 'r') as file: xml_content = file.read()
            tests = json.loads(xml_content)
            print(f'\n **** {len(tests)} tests loaded ****\n\n')
            simulation(tests)
        except: raise(Exception('JSON not accepted'))
    else:
        simulation()