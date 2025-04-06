import configs.configs as configs
from models.client import Client
import time

class TrafficLightClient(Client):
    def __init__(self, host : str, port : int, keepalive : int, subscriber_topic : str, publisher_topic : str):
        super().__init__(host, port, keepalive, subscriber_topic, publisher_topic)

    def subscribe_callback(client, userdata, flags, rc):
        Client.subscribe_callback(client, userdata, flags, rc)


if __name__ == "__main__":
    trafficLightClient = TrafficLightClient(**configs.mqtt_broker_trafficlight_client_config)
    trafficLightClient.connect_to_broker()
    while True: time.sleep(0.1)