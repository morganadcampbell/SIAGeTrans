from databaseController import DatabaseController, DatabaseObject, EventType
from datetime import datetime

databaseController = DatabaseController()

# event = databaseController.select('events', 1)
# print(event.__dict__)

# row = [0, 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Null', 'Teste', 1]
# event = DatabaseObject('events', row)
# print(event.__dict__)
# print(databaseController.insert(event))
# print(event.__dict__)

# event = DatabaseObject('events', [3])
# print(event.__dict__)
# print(databaseController.delete(event))

# event = databaseController.select('events', 1)
# print(event.__dict__)
# event.id_eventtype = EventType.PARTIAL_ROAD_CLOSURE.value
# print(event.__dict__)
# databaseController.update(event)
# event = databaseController.select('events', 1)
# print(event.__dict__)

