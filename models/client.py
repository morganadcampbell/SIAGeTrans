import os, sys
sys.path.insert(1, "/".join(os.path.realpath(__file__).split("/")[0:-2])) ## adding folders to path

import paho.mqtt.client as mqttclient
import configs.configs as configs
import time

class Client:
    __subscriber_topic = None
    __publisher_topic = None

    def __init__(self, host : str, port : int, keepalive : int = 60, subscriber_topic : str = None, publisher_topic : str = None):
        self.__host = host
        self.__port = port
        self.__keepalive = keepalive
        Client.__subscriber_topic = subscriber_topic
        Client.__publisher_topic = publisher_topic

    @staticmethod
    def connection_callback(client, userdata, flags, rc):
        if rc == 0:
            print(f'Client started connection to Broker. Client = {client}')
            if Client.__subscriber_topic: client.subscribe(Client.__subscriber_topic)
        else:
            print(f'Client closed connection to Broker. Código = {rc}')

    @staticmethod
    def subscribe_callback(client, userdata, mid, granted_qos):
        print(f'Client subscribed to {Client.__subscriber_topic} with qos = {granted_qos}.')

    @staticmethod
    def message_callback(client, userdata, message):
        print(f'Client received a message: {message.payload}')
    
    def connect_to_broker(self):
        client = mqttclient.Client()
        client.on_connect = self.__class__.connection_callback
        client.on_subscribe = self.__class__.subscribe_callback
        client.on_message = self.__class__.message_callback
        client.connect(host=self.__host, port=self.__port, keepalive=self.__keepalive)
        client.loop_start()


if __name__ == "__main__": ## listener model
    client = Client(**configs.mqtt_broker_default_client_config)
    client.connect_to_broker()
    while True: time.sleep(0.1)