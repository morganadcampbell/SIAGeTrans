from models.databaseObject import DatabaseObject
from models.DataProvisionStructure import DataProvisionStructure
from models.client import Client
import configs.configs as configs
import pickle

class TSCClient(Client):
    __controller = None
    def __init__(self, controller):
        clientConfigs = configs.mqtt_broker_tsccontroller_client_config
        clientConfigs['client_name'] = clientConfigs.get('client_name') + '_' + str(controller.intersectionId) # subscribe as 'TSCController_<id>'
        clientConfigs['subscriber_topic'] = '/' + controller.region + clientConfigs.get('subscriber_topic') # subscribe to topic '/<region code>/dataProvision'
        clientConfigs['publisher_topic'] = '/' + controller.region + clientConfigs.get('publisher_topic') # publish to topic '/<region code>/timeUpdates'
        super().__init__(**clientConfigs)
        TSCClient.__controller = controller
        
    def messageHandler(client, userdata, message):
        Client.messageHandler(client, userdata, message)
        try:
            data = pickle.loads(message.payload)
            if type(data) != list: raise Exception(f'Received data is not a list')
            for d in data: raise Exception(f'Received data is not a list of dictionary') if type(d) != DataProvisionStructure else None
            TSCClient.__controller.adapt(data)
        except pickle.UnpicklingError as e: # raise error if data is not correctly pickled
            print(f"Error unpickling message: {e}")
        except Exception as e:
            print(e)

class TSCController:
    def __init__(self, controllerId : str, username : str, password : str, ca_certificate : str, client_certificate : str, client_key : str):
        self.controllerId = controllerId
        self.__username = username
        self.__password = password
        self.__ca_certificate = ca_certificate
        self.__client_certificate = client_certificate
        self.__client_key = client_key
        self.__databaseController = DatabaseObject()
    
    def adapt(self, data : list[DataProvisionStructure]):
        # self.__databaseController
        pass #run adaptation on received Data TODO

    def updateTimes(self, intersectionId : int, phasesIds : tuple[int], greenTimes : tuple[int]):
        # publish new times
        tscClient = TSCClient(self)
        tscClient.setSecureConnection(self.__username, self.__password,self.__ca_certificate,self.__client_certificate,self.__client_key)
        tscClient.connectToBroker()
        message = intersectionId + '/'+ '/'.join(map(str, sum(list(zip(phasesIds, greenTimes)), ())))
        tscClient.publish(message)
        tscClient.disconnectFromBroker()

    def startManagement(self):
        tscClient = TSCClient(self)
        tscClient.connectToBroker()
        tscClient.loop_forever()
        tscClient.disconnectFromBroker()
        
        