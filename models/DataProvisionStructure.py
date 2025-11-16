class DataProvisionStructure(dict):
    # define a dictionary with expected values
    def __init__(self, *args, **kwargs):
        expectedItems = ['PhaseId',
                         'QueuedVehicles', 'VehiclesEnteringRate', 'VehiclesLeavingRate', 
                         'QueuedPedestrians', 'PedestriansEnteringRate', 'PedestriansLeavingRate', 
                         'EmergencyVehicles']
        for item in expectedItems:
            if item not in kwargs.keys(): raise Exception(f'{item} not found')
            self[item] = kwargs[item]