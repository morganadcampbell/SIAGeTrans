import xml.etree.ElementTree as ET

def getWeightedLaneMetrics(filename : str, floodedLanes : list):
    '''
    Read from lanedata.xml and return lane data
    '''
    #parsing file
    tree = ET.parse(filename)
    root = tree.getroot()
    
    #reading lane info
    lanes = sum([i.findall("lane") for i in root.find("interval").findall("edge")], [])
    timeLossMap = {i.get("id") : i.get("timeLoss") for i in lanes}
    waitingTimeMap = {i.get("id") : i.get("waitingTime") for i in lanes}
    insertedVehicleMap = {i.get("id") : i.get("left") for i in lanes}
    insertedFloodedVehicles = sum([int(y) for x,y in insertedVehicleMap.items() if x in floodedLanes])

    #calculating waitingtime metrics
    floodedWaitingTimeMap = {x : y for x,y in waitingTimeMap.items() if x in floodedLanes}
    totalFloodedWaitingTime = sum([float(x) for x in floodedWaitingTimeMap.values() if x is not None])
    totalWaitingTime = sum([float(x) for x in waitingTimeMap.values() if x is not None])
    averageFloodedWaitingTime = totalFloodedWaitingTime / max(insertedFloodedVehicles, 1)

    #calculating timeloss metrics
    floodedTimeLossMap = {x : y for x,y in timeLossMap.items() if x in floodedLanes}
    totalTimeLoss = sum([float(x) for x in timeLossMap.values() if x is not None])
    totalFloodedTimeLoss = sum([float(x) for x in floodedTimeLossMap.values() if x is not None])
    averageFloodedTimeLoss = totalFloodedTimeLoss / max(insertedFloodedVehicles, 1)

    return timeLossMap,waitingTimeMap,floodedWaitingTimeMap,totalWaitingTime,totalFloodedWaitingTime,averageFloodedWaitingTime,floodedTimeLossMap,totalTimeLoss,totalFloodedTimeLoss,averageFloodedTimeLoss


def getTripsMetrics(filename : str):
    '''
    Read from tripinfo.xml and return trip data
    '''
    #parsing file
    tree = ET.parse(filename)
    root = tree.getroot()

    #pre-setting variables
    EmrgVehicleWaitingTime = 0;EmrgVehicleTimeLoss = 0;EmrgVehicleDuration = 0;EmrgVehicleCount = 0
    totalVehicleWaitingTime = 0;totalVehicleDuration = 0;totalVehicleTimeLoss = 0;vehiclesCount = 0
    CO2Emission = 0;fuelUse = 0
    totalPersonWaitingTime = 0;totalPersonDuration = 0;totalPersonTimeLoss = 0;personsCount = 0

    #reading vehicles info
    vehicles = root.findall('tripinfo')
    for v in vehicles:
        if v.get('vType')=="VIP": #getting Emrg info
            EmrgVehicleWaitingTime += float(v.get('waitingTime'))
            EmrgVehicleTimeLoss += float(v.get('timeLoss'))
            EmrgVehicleDuration += float(v.get('duration'))
            EmrgVehicleCount += 1

        totalVehicleWaitingTime += float(v.get('waitingTime'))
        totalVehicleTimeLoss += float(v.get('timeLoss'))
        totalVehicleDuration += float(v.get('duration'))
        vehiclesCount += 1

        emission = v.find('emissions')
        CO2Emission += float(emission.get('CO2_abs'))
        fuelUse += float(emission.get('fuel_abs'))
    
    #reading vehicles info
    persons = root.findall('personinfo')
    for p in persons:
        totalPersonWaitingTime += float(p.get('waitingTime'))
        totalPersonTimeLoss += float(p.get('timeLoss'))
        totalPersonDuration += float(p.get('duration'))
        personsCount += 1

    #calculating average metrics
    averageEmrgVehicleWaitingTime = EmrgVehicleWaitingTime / max(EmrgVehicleCount,1)
    averageEmrgVehicleTimeLoss = EmrgVehicleTimeLoss / max(EmrgVehicleCount,1)
    averageEmrgVehicleDuration = EmrgVehicleDuration / max(EmrgVehicleCount,1)
    averageVehicleWaitingTime = totalVehicleWaitingTime / vehiclesCount
    averageVehicleTimeLoss = totalVehicleTimeLoss / vehiclesCount
    averageVehicleDuration = totalVehicleDuration / vehiclesCount
    averagePersonWaitingTime = totalPersonWaitingTime / personsCount
    averagePersonTimeLoss = totalPersonTimeLoss / personsCount
    averagePersonDuration = totalPersonDuration / personsCount
    averageCO2Emission = CO2Emission/vehiclesCount
    averageFuelUse = fuelUse/vehiclesCount

    
    return (averageEmrgVehicleWaitingTime,
            averageEmrgVehicleTimeLoss,
            averageEmrgVehicleDuration,
            averageVehicleWaitingTime,
            averageVehicleTimeLoss,
            averageVehicleDuration,
            averagePersonWaitingTime,
            averagePersonTimeLoss,
            averagePersonDuration,
            averageCO2Emission,
            averageFuelUse,
            EmrgVehicleCount,
            vehiclesCount,
            personsCount)