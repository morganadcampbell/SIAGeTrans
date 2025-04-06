import os, sys
sys.path.insert(1, "/".join(os.path.realpath(__file__).split("/")[0:-2])) ## adding folders to path

import paho.mqtt.client as mqttclient
import configs.configs as configs
import time

class Client:
    __subscriber_topic = None
    __publisher_topic = None
    __client_name = None

    def __init__(self, host : str, port : int, qos : int = 0, keepalive : int = 60, client_name : str = "Default", subscriber_topic : str = None, publisher_topic : str = None):
        self.__host = host
        self.__port = port
        self.__qos = qos
        self.__keepalive = keepalive
        Client.__client_name = client_name
        Client.__subscriber_topic = subscriber_topic
        Client.__publisher_topic = publisher_topic

    def connection_callback(client, userdata, flags, rc):
        if rc == 0:
            print(f'Client {Client.__client_name} started connection to Broker. Client = {client}')
            if Client.__subscriber_topic: client.subscribe(Client.__subscriber_topic)
        else:
            print(f'Client {Client.__client_name} failed connecting to Broker. Código = {rc}')

    def subscribe_callback(client, userdata, mid, granted_qos):
        print(f'Client {Client.__client_name} subscribed to {Client.__subscriber_topic} with qos = {granted_qos}.')

    def message_callback(client, userdata, message):
        print(f'Client {Client.__client_name} received a message: {message.payload} from {message.topic}.')
 
    def publish_callback(client, userdata, mid):
        print(f'Client {Client.__client_name} published a message.')
    
    def connect_to_broker(self):
        self.__client = mqttclient.Client(client_id=Client.__client_name)
        self.__client.on_connect = self.__class__.connection_callback
        self.__client.on_subscribe = self.__class__.subscribe_callback
        self.__client.on_message = self.__class__.message_callback
        self.__client.on_publish = self.__class__.publish_callback
        self.__client.connect(host=self.__host, port=self.__port, keepalive=self.__keepalive)
        self.__client.loop_start()

    def disconnect_from_broker(self) -> int:
        try:
            self.__client.loop_stop()
            self.__client.disconnect()
            print(f"Client {Client.__client_name} disconnected from broker.")
            return 1
        except:
            raise Exception(f"Client {Client.__client_name} failed to disconnect from broker.")
    
    def publish(self, message : str) -> int:
        if Client.__publisher_topic:
            self.__client.publish(topic=Client.__publisher_topic, payload=message, qos=self.__qos)
            return 1
        else: raise Exception(f"Client {Client.__client_name} does not have a publisher_topic defined.")


if __name__ == "__main__": ## test
    client = Client(**configs.mqtt_broker_default_client_config)
    client.connect_to_broker()
    time.sleep(10)
    client.disconnect_from_broker()