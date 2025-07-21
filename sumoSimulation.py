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
'RunAdaptation' : False,                   ###
'MinimumTime' : 15,                        ###
'MaximumTime' : 45,                        ###
'CurrentTemperature' : 20,                 ###
'MaxTemperature' : 30,                     ###
'MinTemperature' : 10,                     ###
'EmergencyVehiclePriorization' : 0,        ### 0 False; 1 True
'EmrgVhcAdaptationInterval' : 10,          ###
'FloodingPriorization' : 0,                ###
'WeatherPriorization' : 0,                 ###
'personPerCarFactor' : 1.54,               ###
'trafficImbalanceFactor' : 0,              ### How many vehicles will be added in each iteration (set 0 for balanced traffic)
'trafficImbalanceFrequency' : 1000,        ### How many steps between each iteration of inserting vehicles (unbalanced traffic distribution)
'MaximumVehicleSpeed' : 16.67,  #(60km/h)  ### Regular vehicle speed
'floodedVehicleSpeed' : 4.17,   #(15km/h)  ### 
'floodedLanes' : ['E1_2', 'E1_1', 'E3_2']  ###
}                                          ###
##############################################
##############################################

def simulation(tests : list[dict] = [simulationParams] ):
    for i in range(len(tests)):
        print(f'\n **** Running test {i+1}/{len(tests)} ****\n\n')
        t = tests[i]
        #setting simulation simulationParams
        sumo_binary = sumolib.checkBinary('sumo') # or 'sumo-gui' for GUI
        currentDatetime = datetime.datetime.now()
        logfileComplement = currentDatetime.strftime("%Y%m%d_%H%M%S")
        sumoCmd = [sumo_binary, "-c", "sumo_simulation/sumo_elements/test.sumocfg", 
                    "--duration-log.statistics", 
                    "--tripinfo-output", "sumo_simulation/sumo_elements/metrics/" + logfileComplement + "_tripinfo_log.xml", "--device.emissions.probability", "1.0",
                    "--log", "sumo_simulation/sumo_elements/metrics/" + logfileComplement + "_metrics.log"]

        ## start simulation
        runSimulation(sumoCmd, t)

        #renaming log file
        os.rename("sumo_simulation/sumo_elements/metrics/lanedata.xml", "sumo_simulation/sumo_elements/metrics/" + logfileComplement + "_lanedata.xml")

        #parsing logfiles
        timeLossMap,waitingTimeMap,floodedWaitingTimeMap,totalWaitingTime,totalFloodedWaitingTime,averageFloodedWaitingTime,floodedTimeLossMap,totalTimeLoss,totalFloodedTimeLoss,averageFloodedTimeLoss = getWeightedLaneMetrics("sumo_simulation/sumo_elements/metrics/" + logfileComplement + "_lanedata.xml", t.get('floodedLanes')) #getting metrics
        averageEmrgVehicleWaitingTime,averageEmrgVehicleTimeLoss,averageEmrgVehicleDuration,averageVehicleWaitingTime,averageVehicleTimeLoss,averageVehicleDuration,averagePersonWaitingTime,averagePersonTimeLoss,averagePersonDuration,averageCO2Emission,averageFuelUse,EmrgVehicleCount,vehiclesCount,personsCount = getTripsMetrics("sumo_simulation/sumo_elements/metrics/" + logfileComplement + "_tripinfo_log.xml") #getting metrics

        #calculating metrics
        WeightedTimeLoss = ((vehiclesCount * averageVehicleTimeLoss) + (personsCount * averagePersonTimeLoss)) / (vehiclesCount + personsCount)
        WeightedDuration = ((vehiclesCount * averageVehicleDuration) + (personsCount * averagePersonDuration)) / (vehiclesCount + personsCount)
        WeightedWaitingTime = ((vehiclesCount * averageVehicleWaitingTime) + (personsCount * averagePersonWaitingTime)) / (vehiclesCount + personsCount)
        VehiclesPerSecondInbalance = t.get('trafficImbalanceFactor') / t.get('trafficImbalanceFrequency')

        #calculating weather info
        WeatherVariance = (t.get('CurrentTemperature') - ((t.get('MaxTemperature') + t.get('MinTemperature'))/2)) ** 2
        WeatherVariationFactor = abs(t.get('CurrentTemperature') - ((t.get('MaxTemperature') + t.get('MinTemperature'))/2) ) / ((t.get('MaxTemperature') - t.get('MinTemperature'))/2)

        #including simulation info to metrics.log
        with open("sumo_simulation/sumo_elements/metrics/" + logfileComplement + "_metrics.log", 'a') as file: 
            file.write("\n-----------------------------------------------------------\n**** Adding simulation info from Sumo Controller ****\n")
            file.write(f'RunAdaptation= {t.get('RunAdaptation')}\nMinimumTime= {t.get('MinimumTime')}\nMaximumTime= {t.get('MaximumTime')}\nCurrentTemperature= {t.get('CurrentTemperature')}\nMaxTemperature= {t.get('MaxTemperature')}\nMinTemperature= {t.get('MinTemperature')}\nEmergencyVehiclePriorization= {t.get('EmergencyVehiclePriorization')}\nFloodingPriorization= {t.get('FloodingPriorization')}\nWeatherPriorization= {t.get('WeatherPriorization')}\
                        \npersonPerCarFactor= {t.get('personPerCarFactor')}\nMaximumVehicleSpeed= {t.get('MaximumVehicleSpeed')}\nfloodedVehicleSpeed= {t.get('floodedVehicleSpeed')}\nfloodedLanes= {t.get('floodedLanes')}\n{defaultVehicleFlowProbability= }\n{emrgVehicleFlowProbability= }\n{pedestrianFlowProbability= }\
                        \n{adaptationInterval= }\n{numberOfPhases= }\n{fixedPhaseTime= }\n{waitingTime= }\n{cicleFullTime= }\n{edges= }\n{crosswalk= }\n{entrySensors= }\n{exitSensors= }\n{entrySensorsPerPhase= }\n{exitSensorsPerPhase= }\
                        \n{lanePerPhase= }\n{crosswalkPerPhase= }\n{PeopleEdgePerPhase= }\n{trafficLightTimes= }\n{VehiclesPerSecondInbalance= }\ntrafficImbalanceFrequency= {t.get('trafficImbalanceFrequency')}\ntrafficImbalanceFactor= {t.get('trafficImbalanceFactor')}\
                        \n{WeightedTimeLoss= }\n{WeightedDuration= }\n{WeightedWaitingTime= }\n{WeatherVariance= }\n{WeatherVariationFactor= }\
                        \n{timeLossMap= }\n{waitingTimeMap= }\n{floodedWaitingTimeMap= }\n{totalWaitingTime= }\n{totalFloodedWaitingTime= }\n{averageFloodedWaitingTime= }\
                        \n{floodedTimeLossMap= }\n{totalTimeLoss= }\n{totalFloodedTimeLoss= }\n{averageFloodedTimeLoss= }\
                        \n{averageEmrgVehicleWaitingTime= }\n{averageEmrgVehicleTimeLoss= }\n{averageEmrgVehicleDuration= }\n{averageVehicleWaitingTime= }\n{averageVehicleTimeLoss= }\n{averageVehicleDuration= }\n{averagePersonWaitingTime= }\n{averagePersonTimeLoss= }\n{averagePersonDuration= }\n{averageCO2Emission= }\n{averageFuelUse= }\n{EmrgVehicleCount= }\n{vehiclesCount= }\n{personsCount= }')

        #inserting simulation data into simulation.log
        with open("sumo_simulation/simulation.log", 'a+') as file:
            file.write(f'**** Simulation Results from {currentDatetime.strftime("%d/%m/%Y at %H:%M:%S")} ****\n')
            file.write(f'**Comparative Metrics**\n\t{WeightedTimeLoss= }\n\t{WeightedDuration= }\n\t{WeightedWaitingTime= }\n\t{averageCO2Emission= }\n\t{averageFuelUse= }\n\t{averageFloodedTimeLoss= }\n\t{averageEmrgVehicleWaitingTime= }\n\t{averageEmrgVehicleTimeLoss= }\n\t{averageEmrgVehicleDuration= }\n\t{averageFloodedWaitingTime= }\n\t{averageFloodedTimeLoss= }\n\t{averageEmrgVehicleWaitingTime= }\n\t{averageEmrgVehicleTimeLoss= }\n\t{averageEmrgVehicleDuration= }\n\t{averageVehicleWaitingTime= }\n\t{averageVehicleTimeLoss= }\n\t{averageVehicleDuration= }\n\t{averagePersonWaitingTime= }\n\t{averagePersonTimeLoss= }\n\t{averagePersonDuration= }\n\n')
            file.write(f'**Simulation Parameters**\n\tRunAdaptation= {t.get('RunAdaptation')}\n\t{VehiclesPerSecondInbalance= }\n\ttrafficImbalanceFactor= {t.get('trafficImbalanceFactor')}\n\ttrafficImbalanceFrequency= {t.get('trafficImbalanceFrequency')}\n\tEmergencyVehiclePriorization= {t.get('EmergencyVehiclePriorization')}\n\tFloodingPriorization= {t.get('FloodingPriorization')}\n\tWeatherPriorization= {t.get('WeatherPriorization')}\n\n')
            file.write(f'**Simulation Data**\n\t{WeatherVariance= }\n\t{WeatherVariationFactor= }\n\t{timeLossMap= }\n\t{waitingTimeMap= }\n\t{floodedWaitingTimeMap= }\n\t{totalWaitingTime= }\n\t{totalFloodedWaitingTime= }\n\t{floodedTimeLossMap= }\n\t{totalTimeLoss= }\n\t{totalFloodedTimeLoss= }\n\t{EmrgVehicleCount= }\n\t{vehiclesCount= }\n\t{personsCount= }\n\n')
            file.write('Full Metrics at: ' + "sumo_simulation/sumo_elements/metrics/" + logfileComplement + "_metrics.log\n")
            file.write('LaneArea Metrics at: ' + "sumo_simulation/sumo_elements/metrics/" + logfileComplement + "_lanedata.xml\n")
            file.write('Trip Metrics at: ' + "sumo_simulation/sumo_elements/metrics/" + logfileComplement + "_tripinfo_log.xml\n")
            file.write("--------------------------------------------------------\n")

        #inserting simulation data into simulation.csv
        with open("sumo_simulation/simulation.csv", 'a+') as file:
            file.seek(0) #writing header if needed
            if file.readline() == '': file.write(f'RunAdaptation;EmergencyVehiclePriorization;FloodingPriorization;WeatherPriorization;MinimumTime;MaximumTime;CurrentTemperature;MaxTemperature;MinTemperature;EmrgVhcAdaptationInterval;personPerCarFactor;trafficImbalanceFactor;trafficImbalanceFrequency;MaximumVehicleSpeed;floodedVehicleSpeed;floodedLanes;WeightedTimeLoss;WeightedDuration;WeightedWaitingTime;averageCO2Emission;averageFuelUse;averageFloodedTimeLoss;averageEmrgVehicleWaitingTime;averageEmrgVehicleTimeLoss;averageEmrgVehicleDuration;averageFloodedWaitingTime;averageFloodedTimeLoss;averageEmrgVehicleWaitingTime;averageEmrgVehicleTimeLoss;averageEmrgVehicleDuration;averageVehicleWaitingTime;averageVehicleTimeLoss;averageVehicleDuration;averagePersonWaitingTime;averagePersonTimeLoss;averagePersonDuration;timeLossMap;waitingTimeMap;floodedWaitingTimeMap;totalWaitingTime;totalFloodedWaitingTime;floodedTimeLossMap;totalTimeLoss;totalFloodedTimeLoss;EmrgVehicleCount;vehiclesCount;personsCount;VehiclesPerSecondInbalance;WeatherVariance;WeatherVariationFactor\n')
            file.seek(io.SEEK_END) #appending data to the file
            file.write(f'{t.get('RunAdaptation')};{t.get('EmergencyVehiclePriorization')};{t.get('FloodingPriorization')};{t.get('WeatherPriorization')};{t.get('MinimumTime')};{t.get('MaximumTime')};{t.get('CurrentTemperature')};{t.get('MaxTemperature')};{t.get('MinTemperature')};{t.get('EmrgVhcAdaptationInterval')};{t.get('personPerCarFactor')};{t.get('trafficImbalanceFactor')};{t.get('trafficImbalanceFrequency')};{t.get('MaximumVehicleSpeed')};{t.get('floodedVehicleSpeed')};{t.get('floodedLanes')};{WeightedTimeLoss};{WeightedDuration};{WeightedWaitingTime};{averageCO2Emission};{averageFuelUse};{averageFloodedTimeLoss};{averageEmrgVehicleWaitingTime};{averageEmrgVehicleTimeLoss};{averageEmrgVehicleDuration};{averageFloodedWaitingTime};{averageFloodedTimeLoss};{averageEmrgVehicleWaitingTime};{averageEmrgVehicleTimeLoss};{averageEmrgVehicleDuration};{averageVehicleWaitingTime};{averageVehicleTimeLoss};{averageVehicleDuration};{averagePersonWaitingTime};{averagePersonTimeLoss};{averagePersonDuration};{timeLossMap};{waitingTimeMap};{floodedWaitingTimeMap};{totalWaitingTime};{totalFloodedWaitingTime};{floodedTimeLossMap};{totalTimeLoss};{totalFloodedTimeLoss};{EmrgVehicleCount};{vehiclesCount};{personsCount};{VehiclesPerSecondInbalance};{WeatherVariance};{WeatherVariationFactor}\n')

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