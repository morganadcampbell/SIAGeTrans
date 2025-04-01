from databaseController import DatabaseController
from datetime import datetime

databaseController = DatabaseController()
# event = databaseController.select('events', 1)
# print(event.__dict__)

# row = (1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Null', 'Teste', 1)
# print(databaseController.insert('events', row))

# print(databaseController.delete('events', 2))


# event.id_eventtype = 1
# event = databaseController.update('events', event)
# event = databaseController.select('events', 1)
# print(event.__dict__)