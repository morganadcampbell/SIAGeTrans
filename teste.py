import cv2
import json
import numpy as np
from ultralytics import YOLO
from shapely.geometry import Polygon
from video_detection.auxiliar.Tracker import PersonTracker,VehiclesTracker
from video_detection.auxiliar.Hitbox import Hitbox

def updateTrackers(preset = 1):  
    tracker = VehiclesTracker(Polygon(hitboxes[preset].queuedArea), Polygon(hitboxes[preset].trackedOut), Polygon(hitboxes[preset].trackedIn))
    ptracker = PersonTracker(list(map(Polygon, hitboxes[preset].trackedPedestrians)))
    return tracker,ptracker

def drawHitboxMask(frame, hitbox):
    shapes = np.zeros_like(frame, np.uint8) # Initialize blank mask image of same dimensions for drawing the shapes
    cv2.fillPoly(shapes, [np.array(hitbox.queuedArea, np.int32)], (0, 0, 255))
    cv2.fillPoly(shapes, [np.array(hitbox.trackedOut, np.int32)], (255, 0, 0))
    cv2.fillPoly(shapes, [np.array(hitbox.trackedIn, np.int32)], (255, 0, 0))
    for p in hitbox.trackedPedestrians:
        cv2.fillPoly(shapes, [np.array(p, np.int32)], (0, 255, 0))
    return shapes

# parameters
UPDATE_RATE = 2 #frames
CONF_THRESH = 0.55
DIST_THRESH = 80

# hitbox data for each preset
with open('video_detection/data/presetsHitbox.json', 'r') as f:
    data = json.load(f, object_hook=lambda d: Hitbox(**d))
    hitboxes = {h.preset : h for h in data}
tracker,ptracker = None,None

# model will be downloaded on the first run
model = YOLO('video_detection/yolo_model/yolov8n.pt')
# loading video sample
video = cv2.VideoCapture("video_detection/data/video_30sec.mp4")

#writer
# width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH) + 0.5)
# height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT) + 0.5)
# size = (width, height)
# fourcc = cv2.VideoWriter_fourcc(*'MP4V')
# out = cv2.VideoWriter('output.mp4', fourcc, 20.0, size)

# preseting variables
count = UPDATE_RATE
framecount = 0
currentpreset = 1
results = None
detected_vehicles_data,detected_pedestrians_data,detected_object = [],[],[]

if video.isOpened():
    ret, frame = video.read()
    tracker,ptracker = updateTrackers(currentpreset)
    shapes = drawHitboxMask(frame, hitboxes[currentpreset])
    while True:
        count += 1
        framecount += 1
        ret, frame = video.read()
        if not ret: break

        # updating object detection
        if count > UPDATE_RATE:
            detected_object.clear()
            detected_vehicles_data.clear()
            detected_pedestrians_data.clear()
            count = 0
            results = model(frame)

            # listing detected objects
            for r in results: 
                for box in r.boxes:
                    coordinates = box.xyxy.tolist()[0]
                    x1, y1, x2, y2 = int(coordinates[0]), int(coordinates[1]), int(coordinates[2]), int(coordinates[3])
                    pol = Polygon([(x1,y1), (x2,y1), (x2,y2),(x1,y2)])
                    conf = round(float(box.conf[0]),2) # Confidence score
                    clsname = model.names.get(int(box.cls[0]))
                    detected_object.append([x1, y1, x2, y2, conf, clsname, pol])
            # endfor (listing detected objects)
            detected_vehicles_data = tracker.updateCouting(detected_object)
            detected_pedestrians_data = ptracker.updateCouting(detected_object)
        
        # drawing objects boxes from results
        for obj in detected_vehicles_data:
            cv2.rectangle(frame, (obj.x1, obj.y1), (obj.x2, obj.y2), (0, 255, 0), 2)
            cv2.putText(frame, "ID" + str(obj.id), (obj.x1, obj.y1 + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        for obj in detected_pedestrians_data:
            cv2.rectangle(frame, (obj.x1, obj.y1), (obj.x2, obj.y2), (0, 255, 355), 2)
            cv2.putText(frame, "ID" + str(obj.id), (obj.x1, obj.y1 + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        # endfor (drawing objects boxes from results)
        
        # Adding hitboxes mask to frame
        alpha = 0.3
        mask = shapes.astype(bool)
        frame[mask] = cv2.addWeighted(frame, alpha, shapes, 1 - alpha, 0)[mask]
        cv2.putText(frame, "Vehicles In: " + str(len(tracker.getArrivingCount())), (20,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Vehicles Out: " + str(len(tracker.getLeavingCount())), (20,60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Vehicles Queued: " + str(tracker.getQueueCount()), (20,90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Pedestrians Queued: " + str(ptracker.getIdCount()), (20,120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        #update frame
        cv2.imshow("video", frame)
        # out.write(frame)

        # if framecount > 350: break
        if cv2.waitKey(1) == ord('q'): 
            raise(Exception("Video Stopped"))

    # endwhile
    video.release()
    # out.release()
    cv2.destroyAllWindows()
else: raise(Exception("Video could not be opened"))

