from models.client import Client
import configs.configs as configs
import time

class IntersectionClient(Client):
    __controller = None
    def __init__(self, controller):
        clientConfigs = configs.mqtt_broker_intersection_client_config
        clientConfigs['client_name'] = f"{clientConfigs.get('client_name')}_{controller.intersectionId}" # subscribe as 'intersection_<id>'
        clientConfigs['subscriber_topic'] = f"/{controller.region}{clientConfigs.get('subscriber_topic')}" # subscribe to topic '/<region code>/timeUpdates'
        super().__init__(**clientConfigs)
        IntersectionClient.__controller = controller

    def messageHandler(client, userdata, message):
        Client.messageHandler(client, userdata, message)
        payload = message.payload.decode('ascii').split('/') # receives messages as '<intersectionId>/<phase1_Id>/<phase1_GreenTime>/.../<phaseN_Id>/<phaseN_GreenTime>'
        intersectionId = payload.pop(0)
        if intersectionId == IntersectionClient.__controller.intersectionId and all(id in IntersectionClient.__controller.getPhasesId() for id in payload[::2]):
            IntersectionClient.__controller.updateTimes(dict(zip(payload[::2], payload[1::2])))

class TrafficLightController:
    def __init__(self, intersectionId : int, region : str, phases : list[DatabaseObject]):
        self.intersectionId = intersectionId
        self.region = region
        self.__phases = {str(x.getId()) : x for x in phases}
        self.__active = False

    def getPhasesId(self) -> list[str]: return self.__phases.keys()

    def updateTimes(self, phasesNewTimes : dict):
        print(f"\nUpdating intersection_{self.intersectionId} with green times as:")
        for id,time in phasesNewTimes.items():
            print(f"\tPhase_{id} with green times as: {time}")
            self.__phases[id].nr_green_duration = time # updating phase object
        
    def startManagement(self):
        self.__active = True
        trafficLightClient = IntersectionClient(self)
        trafficLightClient.connectToBroker()
        while self.__active:
            time.sleep(60)
        trafficLightClient.disconnectFromBroker()