import time
from shapely.geometry import Polygon

class ObjectsTracker:
    def __init__(self):
        self.trackedAreaPolygons = []
        self._starting_time,self._ending_time =  time.time(),0.0 #in seconds
        self._queued,self._queue_in,self._queue_out,self._last_queued = set(),set(),set(),set()
    
    # @classmethod
    def getObjectPolygon(self, x, y, w, h): return Polygon([(x,y), (x+w, y), (x+w, y+h), (x, y+h)])
    def getEnteringList(self) -> list: return self._queue_in
    def getEnteringCount(self) -> int: return len(self._queue_in)
    def getLeavingList(self) -> list: return self._queue_out
    def getLeavingCount(self) -> int: return len(self._queue_out)
    def getQueueCount(self) -> int: return len(self._queue_in) - len(self._queue_out) # entered but did not leave

    def getQueueEnteringRate(self) -> float:
        self._ending_time = time.time()
        return float(len(self._queue_in))/(self._ending_time - self._starting_time)

    def getQueueLeavingRate(self) -> float:
        self._ending_time = time.time()
        return float(len(self._queue_out))/(self._ending_time - self._starting_time)

    def updateCouting(self, objects_boxes : dict) -> None:
        self._last_queued = self._queued.copy()
        self._queued.clear()
        for id in objects_boxes.keys(): # for each object detected
            (x, y, w, h)  = objects_boxes[id]
            pol = self.getObjectPolygon(x, y, w, h)
            for polarea in self.trackedAreaPolygons:
                if pol.intersects(polarea): self._queued.add(id)
        self._queue_in = self._queue_in.union(self._queued) # update objects entering trackedZone
        self._queue_out = self._queue_out.union(self._last_queued.difference(self._queued)) # update objects leaving trackedZone
        self._queue_out = self._queue_out.difference(self._queued) # reentering objects

class PedestrianTracker(ObjectsTracker):
    def __init__(self, sidwalkAreas):
        super().__init__()
        for sidewalk in sidwalkAreas:
            self.trackedAreaPolygons.append(Polygon(sidewalk))

class VehicleTracker(ObjectsTracker):
    def __init__(self, laneArea):
        super().__init__()
        self.trackedAreaPolygons.append(Polygon(laneArea))

    def getQueuedEmergencyVehicles(self):
        return 0 #TODO
