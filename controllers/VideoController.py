import cv2
import time
import numpy as np
from shapely.geometry import Polygon
from video_detection.auxiliar.PresetRecognition import *

class VideoController:    
    def drawHitboxMask(frame, hitbox):
        shapes = np.zeros_like(frame, np.uint8) # Initialize blank mask image of same dimensions for drawing the shapes
        cv2.fillPoly(shapes, [np.array(hitbox.laneArea, np.int32)], (0, 0, 255))
        for p in hitbox.sidewalkArea:
            cv2.fillPoly(shapes, [np.array(p, np.int32)], (0, 255, 0))
        return shapes
    
    def getCameraState(frame, last_gray_frame, orb_detector, reference_descriptors, video_state, currentpreset, testing_preset, confirmation_counter):
        processing_frame = cv2.resize(frame, (PROCESSING_WIDTH, PROCESSING_HEIGHT))
        gray_frame = cv2.cvtColor(processing_frame, cv2.COLOR_BGR2GRAY)
        camera_stabiity = not simpleMovementDetection(last_gray_frame, gray_frame)
        last_gray_frame = gray_frame.copy()
        if not camera_stabiity:
            video_state = "Searching Preset"
            currentpreset = testing_preset = None
            confirmation_counter = 0
        if video_state == "Searching Preset" and camera_stabiity:
            identifiedPreset, n_matches = identify_preset_features(gray_frame, orb_detector, reference_descriptors)
            if identifiedPreset == testing_preset:
                confirmation_counter += 1
            else:
                testing_preset = identifiedPreset
                confirmation_counter = 1 if identifiedPreset else 0
            if confirmation_counter >= CONFIRMATION_THRESHOLD and identifiedPreset:
                currentpreset = testing_preset
                video_state = "Preset Set"
        status_text = (
                f"Current Preset: {currentpreset} (Stable)" if video_state == "Preset Set"
                else f"Testing: {testing_preset} ({confirmation_counter}/{CONFIRMATION_THRESHOLD})"
                if testing_preset else "Moving..."
            )
        return last_gray_frame, video_state, currentpreset, testing_preset, status_text, confirmation_counter



class ObjectsTracker:
    def __init__(self):
        self.trackedAreaPolygons = []
        self._starting_time,self._ending_time =  time.time(),0.0 #in seconds
        self._queued,self._queue_in,self._queue_out,self._last_queued = set(),set(),set(),set()
    
    # @classmethod
    def getObjectPolygon(self, x, y, w, h): return Polygon([(x,y), (x+w, y), (x+w, y+h), (x, y+h)])
    def getEnteringCount(self) -> int: return len(self._queue_in)
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

class PedestrianTracker(ObjectsTracker):
    def __init__(self, sidwalkAreas):
        super().__init__()
        for sidewalk in sidwalkAreas:
            self.trackedAreaPolygons.append(Polygon(sidewalk))

class VehicleTracker(ObjectsTracker):
    def __init__(self, laneArea):
        super().__init__()
        self.trackedAreaPolygons.append(Polygon(laneArea))

class Hitbox:
    def __init__(self, preset, laneArea : list[list], sidewalkArea : list[list[list]]):
        self.preset = preset
        self.laneArea = laneArea
        self.sidewalkArea = sidewalkArea
