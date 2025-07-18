import xml.etree.ElementTree as ET

def getWeightedMetrics(filename : str):
    '''
    Read from metrics.log and return timeloss and duration data
    '''
    with open(filename, 'r') as file:
        line = file.readline()
        while line[0:9] != ' Inserted' and line: line = file.readline()
        insertedVehicles = int(line.split(' ')[2].strip()); line = file.readline()
        while line[0:9] != ' Inserted' and line: line = file.readline()
        insertedPedestrian = int(line.split(' ')[2].strip()); line = file.readline()
        while line[0:9] != ' Duration' and line: line = file.readline()
        vehicleDuration = float(line.split(' ')[2].strip()); line = file.readline()
        while line[0:9] != ' TimeLoss' and line: line = file.readline()
        vehicleTimeLoss = float(line.split(' ')[2].strip()); line = file.readline()
        while line[0:9] != ' Duration' and line: line = file.readline()
        pedestrianDuration = float(line.split(' ')[2].strip()); line = file.readline()
        while line[0:9] != ' TimeLoss' and line: line = file.readline()
        pedestrianTimeLoss = float(line.split(' ')[2].strip())
    return insertedVehicles,vehicleDuration,vehicleTimeLoss,insertedPedestrian,pedestrianDuration,pedestrianTimeLoss

def getWeightedLaneMetrics(filename : str, floodedLanes : list):
    '''
    Read from lanedata.xml and return lane data
    '''
    tree = ET.parse(filename)
    root = tree.getroot()
    lanes = sum([i.findall("lane") for i in root.find("interval").findall("edge")], [])
    timeLossMap = {i.get("id") : i.get("timeLoss") for i in lanes}
    waitingTimeMap = {i.get("id") : i.get("waitingTime") for i in lanes}
    floodedWaitingTimeMap = {x : y for x,y in waitingTimeMap.items() if x in floodedLanes}
    totalWaitingTime = sum([float(x) for x in waitingTimeMap.values() if x is not None])
    totalFloodedWaitingTime = sum([float(x) for x in floodedWaitingTimeMap.values() if x is not None])
    adjustedFloodedWaitingTime = totalFloodedWaitingTime / totalWaitingTime
    floodedTimeLossMap = {x : y for x,y in timeLossMap.items() if x in floodedLanes}
    totalTimeLoss = sum([float(x) for x in timeLossMap.values() if x is not None])
    totalFloodedTimeLoss = sum([float(x) for x in floodedTimeLossMap.values() if x is not None])
    adjustedFloodedTimeLoss = totalFloodedTimeLoss / totalTimeLoss
    return timeLossMap,waitingTimeMap,floodedWaitingTimeMap,totalWaitingTime,totalFloodedWaitingTime,adjustedFloodedWaitingTime,floodedTimeLossMap,totalTimeLoss,totalFloodedTimeLoss,adjustedFloodedTimeLoss

def getEmissionAndEmrgMetrics(filename : str):
    '''
    Read from tripinfo.xml and return trip data
    '''
    tree = ET.parse(filename)
    root = tree.getroot()
    vehicles = root.findall('tripinfo')
    CO2Emission = 0
    fuelUse = 0
    EmrgWaitingTime = 0
    EmrgTimeLoss = 0
    EmrgDuration = 0
    EmrgCount = 0
    vehicleWaitingTime = 0
    vehiclesCount = 0
    for v in vehicles:
        if v.get('vType')=="VIP": #getting Emrg info
            EmrgWaitingTime += float(v.get('waitingTime'))
            EmrgTimeLoss += float(v.get('timeLoss'))
            EmrgDuration += float(v.get('duration'))
            EmrgCount += 1
        vehicleWaitingTime += float(v.get('waitingTime'))
        emission = v.find('emissions')
        CO2Emission += float(emission.get('CO2_abs'))
        fuelUse += float(emission.get('fuel_abs'))
        vehiclesCount += 1
    EmrgWaitingTimeAvg = EmrgWaitingTime/max(EmrgCount,1)
    EmrgTimeLossAvg = EmrgTimeLoss/max(EmrgCount,1)
    EmrgDurationAvg = EmrgDuration/max(EmrgCount,1)
    vehicleWaitingTimeAvg = vehicleWaitingTime/vehiclesCount
    CO2EmissionAvg = CO2Emission/vehiclesCount
    fuelUseAvg = fuelUse/vehiclesCount
    return CO2EmissionAvg,fuelUseAvg,EmrgWaitingTimeAvg,EmrgTimeLossAvg,EmrgDurationAvg,vehicleWaitingTimeAvg
