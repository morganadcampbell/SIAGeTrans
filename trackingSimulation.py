import cv2
import json
import numpy as np
from ultralytics import YOLO
from shapely.geometry import Polygon
from video_detection.auxiliar.Tracker import PersonTracker,VehiclesTracker
from video_detection.auxiliar.Hitbox import Hitbox
from video_detection.auxiliar.PresetRecognition import *

#auxiliar functions
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


# parameters
CAMERA_UPDATE_RATE = 4 #frames
UPDATE_RATE = 2 #frames
CONF_THRESH = 0.45
DIST_THRESH = 80
PRESET_EXAMPLES = "video_detection/data/presets"

# hitbox data for each preset
with open('video_detection/data/presetsHitbox.json', 'r') as f:
    data = json.load(f, object_hook=lambda d: Hitbox(**d))
    hitboxes = {h.preset : h for h in data}

# model will be downloaded on the first run
model = YOLO('video_detection/yolo_model/yolov8n.pt')
# loading video sample
video = cv2.VideoCapture("video_detection/data/video_1min.mp4")

#writer
width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH) + 0.5)
height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT) + 0.5)
out = cv2.VideoWriter('output.mp4', cv2.VideoWriter_fourcc(*'MP4V'), 20.0, (width, height))

# preseting variables
count = UPDATE_RATE
framecount = 0
currentpreset = 1
detected_vehicles_data,detected_pedestrians_data,detected_object = [],[],[]
video_state = "Searching Preset"
status_text = ""
testing_preset,last_gray_frame = None,None
confirmation_counter = 0
tracker,ptracker,shapes = None,None,None

if video.isOpened():
    orb_detector, reference_descriptors = analyze_presets_reference(PRESET_EXAMPLES) #loading presets
    fps = video.get(cv2.CAP_PROP_FPS) or 30
    delay = max(int(1000 / fps), 10)
    while True:
        count += 1
        framecount += 1
        ret, frame = video.read()
        if not ret: break

        if framecount % CAMERA_UPDATE_RATE == 0: #testing preset
            last_gray_frame, video_state, currentpreset, testing_preset, status_text, confirmation_counter = getCameraState(frame, last_gray_frame, orb_detector, reference_descriptors, video_state, currentpreset, testing_preset, confirmation_counter)

        if video_state != "Preset Set": 
            tracker,ptracker,shapes = None,None,None
            detected_vehicles_data.clear()
            detected_pedestrians_data.clear()
        elif tracker == None or ptracker == None: 
            print(hitboxes, currentpreset)
            shapes = drawHitboxMask(frame, hitboxes[currentpreset]) #loading hitboxs
            tracker,ptracker = updateTrackers(currentpreset) #setting trackers

        # updating object detection
        if count > UPDATE_RATE and video_state == "Preset Set":
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
        
        if shapes is not None: # Adding hitboxes mask to frame
            alpha = 0.3
            mask = shapes.astype(bool)
            frame[mask] = cv2.addWeighted(frame, alpha, shapes, 1 - alpha, 0)[mask]
        cv2.putText(frame, status_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if video_state == "Preset Set" else (0, 0, 255), 2)
        cv2.putText(frame, "Vehicles In: " + str(tracker.getArrivingCount() if tracker else 'n/a') + " (" + ("{:.2f} veic/s".format(tracker.getQueue2DepartureRate()) if tracker else "-") + ")", (20,60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Vehicles Out: " + str(tracker.getLeavingCount() if tracker else 'n/a') + " (" + ("{:.2f} veic/s".format(tracker.getQueueDepartureRate()) if tracker else "-") + ")", (20,90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Vehicles Queued: " + str(tracker.getQueueCount() if tracker else 'n/a'), (20,120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Pedestrians Queued: " + str(ptracker.getIdCount() if ptracker else 'n/a'), (20,150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        #update frame
        cv2.imshow("video", frame)
        out.write(frame)

        # if framecount > 350: break
        if cv2.waitKey(delay) == ord('q'): 
            raise(Exception("Video Stopped"))

    # endwhile
    video.release()
    out.release()
    cv2.destroyAllWindows()
else: raise(Exception("Video could not be opened"))
