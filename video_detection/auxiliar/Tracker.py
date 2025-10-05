import math
import time
from shapely.geometry import Polygon


class Object:
    def __init__(self, x1, y1, x2, y2, conf, classname, polygon, id = None):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.conf = conf
        self.classname = classname
        self.polygon = polygon
        self.id = id

# based on https://github.com/rajith-ravikumar-gwu/people_counter/blob/main/tracker.py
class ObjectsTracker:
    def __init__(self, TrackedAreaPolygon, TrackedClasses = ['car', 'person'], CONF_THRESH = 0.55, DIST_THRESH = 40):
        self._conf_thresh = CONF_THRESH
        self._dist_thresh = DIST_THRESH
        self._trackedAreaPolygon = TrackedAreaPolygon
        self._trackedClasses = TrackedClasses
        self._starting_time,self._ending_time =  time.time(),0.0 #in seconds
        self._objects_ids_count,self._queuedObjectsCount = 0,0
        self._objects_center = {}
        self._queue_in,self._queue_out,self._last_ids_in = set(),set(),set()

    def getIdCount(self) -> int: return self._objects_ids_count

    def getQueueCount(self) -> int: return self._queuedObjectsCount

    def resetCouting(self) -> None:
        self._starting_time = time.time()
        self._ending_time = 0.0
        self._objects_ids_count,self._queuedObjectsCount = 0,0
        self._objects_center = {}
        self._queue_in,self._queue_out,self._last_ids_in = set(),set(),set()
        
    def resetTrackedAreaPolygon(self, TrackedAreaPolygon):
        self._trackedAreaPolygon = TrackedAreaPolygon
        self.resetCouting()

    def getQueueArrivalRate(self) -> float:
        self._ending_time = time.time()
        return float(len(self._queue_in))/(self._ending_time - self._starting_time)

    def getQueueDepartureRate(self) -> float:
        self._ending_time = time.time()
        return float(len(self._queue_out))/(self._ending_time - self._starting_time)

    def updateQueuedObjects(self, objects_boxes) -> int:
        self._queuedObjectsCount = 0
        for obj in objects_boxes: # for each object detected
            x1, y1, x2, y2, conf, clsname, pol = obj
            if conf > self._conf_thresh and clsname in self._trackedClasses and pol.intersects(self._trackedAreaPolygon): # counts queued objects
                self._queuedObjectsCount+=1
        return self._queuedObjectsCount

    def updateTracking(self, objects_boxes, trackedArea = None) -> list[Object]:
        self.updateQueuedObjects(objects_boxes)
        if trackedArea is None: trackedArea = self._trackedAreaPolygon #default
        objects_data = []
        for obj in objects_boxes: # for each object detected
            x1, y1, x2, y2, conf, clsname, pol = obj
            if conf > self._conf_thresh and clsname in self._trackedClasses and pol.intersects(trackedArea): # counts queued objects
                cx, cy = (x1 + (x2 - x1)//2), (y1 + (y2 - y1)//2) # draw its boudingbox
                same_object_detected = False
                for id, pt in self._objects_center.items(): # test proximity to each previously detected objects
                    if math.hypot(cx - pt[0], cy - pt[1]) < self._dist_thresh: # calculating euclidean distance
                        self._objects_center[id] = (cx, cy) # updates object position
                        objects_data.append(Object(x1, y1, x2, y2, conf, clsname, pol, id))
                        same_object_detected = True
                        break
                if not same_object_detected: # adding new object
                    self._objects_center[self._objects_ids_count] = (cx, cy)
                    objects_data.append(Object(x1, y1, x2, y2, conf, clsname, pol, self._objects_ids_count))
                    self._objects_ids_count += 1
        return objects_data
        
    def updateCouting(self, objects_boxes) -> list[Object]:
        objects_data = self.updateTracking(objects_boxes) #updating objects tracking
        self.updateQueuedObjects(objects_boxes) #updating queued couting
        ids_in = set() #list of object's id within tracked area
        for obj in objects_data:
            if obj.polygon.intersects(self._trackedAreaPolygon):
                ids_in.add(obj.id)
        self._queue_in = self._queue_in.union(ids_in) # update objects entering trackedZone
        self._queue_out = self._queue_out.union(self._last_ids_in.difference(ids_in)) # update objects leaving trackedZone
        self._last_ids_in = ids_in
        return objects_data




class VehiclesTracker(ObjectsTracker):
    def __init__(self, trackedArea, leavingArea, arrivingArea, CONF_THRESH = 0.55, DIST_THRESH = 120):
        super().__init__(trackedArea, ['car', 'bus', 'truck', 'motorcycle'], CONF_THRESH, DIST_THRESH)
        self._leavingArea = leavingArea
        self._arrivingArea = arrivingArea
        self._queue_2_in,self._queue_2_out,self._last_ids_2_in = set(),set(),set()

    def getLeavingCount(self) -> int: return len(self._queue_in)
    def getArrivingCount(self) -> int: return len(self._queue_2_in)

    def resetCouting(self) -> None:
        super.resetCouting()
        self._queue_2_in,self._queue_2_out,self._last_ids_2_in = set(),set(),set()
        
    def resetTrackedAreaPolygon(self, TrackedAreaPolygon, leavingArea, arrivingArea):
        self._leavingArea = leavingArea
        self._arrivingArea = arrivingArea
        super().resetTrackedAreaPolygon(TrackedAreaPolygon)

    def getQueue2ArrivalRate(self) -> float:
        self._ending_time = time.time()
        return float(len(self._queue_2_in))/(self._ending_time - self._starting_time)

    def getQueue2DepartureRate(self) -> float:
        self._ending_time = time.time()
        return float(len(self._queue_2_out))/(self._ending_time - self._starting_time)
 
    def updateCouting(self, objects_boxes) -> list[Object]:
        trackedArea = self._leavingArea.union(self._arrivingArea)
        objects_data = self.updateTracking(objects_boxes, trackedArea) #updating objects tracking
        ids_in,ids_2_in = set(),set() #list of object's id within tracked area
        ids_out,ids_2_out = set(),set() #list of object's id no longer within tracked area
        for obj in objects_data:
            if obj.polygon.intersects(self._leavingArea):
                ids_in.add(obj.id)
            elif obj.polygon.intersects(self._arrivingArea):
                ids_2_in.add(obj.id)
        #leaving
        self._queue_in = self._queue_in.union(ids_in) # update objects entering trackedZone
        ids_out = self._last_ids_in.difference(ids_in)
        self._queue_out = self._queue_out.union(ids_out) # update objects leaving trackedZone
        self._last_ids_in = ids_in
        #arriving
        self._queue_2_in = self._queue_2_in.union(ids_2_in) # update objects entering trackedZone
        ids_2_out = self._last_ids_2_in.difference(ids_2_in)
        self._queue_2_out = self._queue_2_out.union(ids_2_out) # update objects leaving trackedZone
        self._last_ids_2_in = ids_2_in
        #removing objects
        for id in ids_out.union(ids_2_out): self._objects_center.pop(id)
        return objects_data



class PersonTracker(ObjectsTracker):
    def __init__(self, trackedAreas : list, CONF_THRESH = 0.55, DIST_THRESH = 30):
        fullTrackedArea = trackedAreas[0]
        for i in range(len(trackedAreas) - 1):
            fullTrackedArea = fullTrackedArea.union(trackedAreas[i])
        super().__init__(fullTrackedArea, ['person'], CONF_THRESH, DIST_THRESH)
