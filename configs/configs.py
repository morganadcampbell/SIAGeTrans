
mysql_connection_config = {
                            "host": "localhost", 
                            "user": "lsiagetrans", 
                            "password": "123abc", 
                            "database": "siagetrans",
                            "auth_plugin": "mysql_native_password"
                          }

mqtt_broker_default_client_config = { 
                        "host": "localhost",
                        "port": 1883,
                        "qos" : 2,
                        "keepalive": 60,
                        "client_name": "Default",
                        "subscriber_topic": None,
                        "publisher_topic": None
                     }

mqtt_broker_trafficlight_client_config = { 
                        "host": "localhost",
                        "port": 1883,
                        "qos" : 0,
                        "keepalive": 60,
                        "client_name": "trafficlight",
                        "subscriber_topic": "/message",
                        "publisher_topic": "/message"
                     }
