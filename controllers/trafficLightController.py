from models.databaseObject import DatabaseObject
from models.client import Client
import configs.configs as configs
import time

class IntersectionClient(Client):
        __controller = None
        def __init__(self, controller):
            clientConfigs = configs.mqtt_broker_intersection_client_config
            clientConfigs['client_name'] = clientConfigs.get('client_name') + '_' + str(controller.id)
            clientConfigs['subscriber_topic'] = '/' + controller.region + clientConfigs.get('subscriber_topic')
            super().__init__(**clientConfigs)
            IntersectionClient.__controller = controller

        def messageHandler(client, userdata, message):
            Client.messageHandler(client, userdata, message)
            payload = message.payload.decode('ascii').split('/')
            managedTrafficLights = IntersectionClient.__controller.getManagedTrafficLightsId()
            if payload[0] in managedTrafficLights:
                IntersectionClient.__controller.updateTimes(payload[0], tuple(payload[1:]))

class TrafficLightController:
    def __init__(self, id : int, region : str, managedTrafficLights : list[DatabaseObject]):
        self.id = id
        self.region = region
        self.__managedTrafficLights = {str(x.getId()) : x for x in managedTrafficLights}
        self.__active = False

    def getManagedTrafficLightsId(self) -> list[str]: return self.__managedTrafficLights.keys()

    def updateTimes(self, id : str, newTimes : tuple[int]):
        trafficlight = self.__managedTrafficLights.get(id)
        print(f"\nUpdating trafficLight_{id} as:\n\tGreenTime: {trafficlight.nr_greentime_s} -> {newTimes[0]}\n\tYellowTime: {trafficlight.nr_yellowtime_s} -> {newTimes[1]}\n\tRedTime: {trafficlight.nr_redtime_s} -> {newTimes[2]}\n")
        self.__managedTrafficLights.get(id).nr_greentime_s = newTimes[0]
        self.__managedTrafficLights.get(id).nr_yellowtime_s = newTimes[1]
        self.__managedTrafficLights.get(id).nr_redtime_s = newTimes[2]

    def startManagement(self):
        self.__active = True
        trafficLightClient = IntersectionClient(self)
        trafficLightClient.connectToBroker()
        while self.__active:
            time.sleep(60)
        trafficLightClient.disconnectFromBroker()