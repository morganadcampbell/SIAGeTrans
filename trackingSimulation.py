import cv2
import json
import time
from ultralytics import YOLO
from controllers.CameraController import *
from video_detection.auxiliar.PresetRecognition import *

###########################################################
######## Adaptation Parameters ############################
simulationParams = {                                    ###
'camera_update_rate': 4,                                ### #frames
'update_rate': 5,                                       ### #frames
'conf_thresh': 0.6,                                    ###
'preset_examples': "video_detection/data/presets",      ###
'desired_classes': [0, 2, 3, 5, 7],                     ### #person, car, motorcycle, bus, truck
'yolo_model': 'video_detection/yolo_model/yolo11n.pt'   ###
}                                                       ###
###########################################################
###########################################################


def trackingSimulation(hitboxes, tests : list[dict] = [simulationParams], export : bool = False ):
    log = open('output.log', 'a') # open log file

    for i in range(len(tests)):
        print(f'\n **** Running test {i+1}/{len(tests)} ****\n\n')
        t = tests[i]

        #logging simulations parameters
        log.write(f'############# Teste {i+1}/{len(tests)} #############\n')
        for k,v in t.items(): log.write(k + ': ' + str(v) + '\n')

        # model will be downloaded on the first run
        model = YOLO(t.get('yolo_model'))
        # loading video sample
        cap = cv2.VideoCapture("video_detection/data/video_1min.mp4")

        # setting up output
        outputvideoname = f'output_test_{int(time.time())}.mp4'
        log.write(f'Output Video Name: {outputvideoname}\n')
        if export: output = cv2.VideoWriter(outputvideoname, cv2.VideoWriter_fourcc(*'mp4v'), 20.0, (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) + 0.5), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) + 0.5)))
        else: output = None

        # preseting variables
        framecount,confirmation_counter = 0,0
        currentpreset,lastpreset = "1",None
        video_state,status_text = "Searching Preset", ""
        testing_preset,last_gray_frame,shapes = None,None,None
        orb_detector, reference_descriptors = analyze_presets_reference(t.get('preset_examples')) #loading presets
        cameraController = None

        if cap.isOpened():
            # fps = cap.get(cv2.CAP_PROP_FPS) or 30
            # delay = max(int(1000 / fps), 10)

            while True:
                framecount += 1
                success, frame = cap.read() # Read a frame from the video
                if not success: break

                if framecount % t.get('camera_update_rate') == 0: #testing preset
                    last_gray_frame, video_state, currentpreset, testing_preset, status_text, confirmation_counter = CameraController.getCameraState(frame, last_gray_frame, orb_detector, reference_descriptors, video_state, currentpreset, testing_preset, confirmation_counter)
                    if currentpreset is not None and currentpreset != lastpreset:
                        lastpreset = currentpreset
                        shapes = CameraController.drawHitboxMask(frame, hitboxes[currentpreset]) #loading hitboxs
                        cameraController = CameraController({'0' : VehicleTracker(hitboxes[currentpreset].laneArea)}, {'0' : PedestrianTracker(hitboxes[currentpreset].sidewalkArea)}) #setting trackers

                if shapes is None and 'Stable' in status_text and currentpreset is not None:
                    shapes = CameraController.drawHitboxMask(frame, hitboxes[currentpreset]) #loading hitboxs
                elif 'Stable' not in status_text or currentpreset is None:
                    shapes = None

                # Run YOLO tracking on the frame, persisting tracks between frames
                result = model.track(frame, classes=t.get('desired_classes'), conf=t.get('conf_thresh'), verbose=False, persist=True)[0]

                # Get the boxes and track IDs
                if result.boxes and result.boxes.is_track:
                    boxes = result.boxes.xywh.cpu()
                    classes = result.boxes.cls.int().cpu().tolist()
                    ids = result.boxes.id.int().cpu().tolist()
                    # updating object detection
                    if framecount % t.get('update_rate') == 0 and video_state == "Preset Set" and cameraController.getVehicleTracker('0') is not None and cameraController.getPedestrianTracker('0') is not None:
                        pedestrians = {id : box for box,id,cls in zip(boxes,ids,classes) if cls in [0]}
                        cameraController.getPedestrianTracker('0').updateCouting(pedestrians)
                        vehicles = {id : box for box,id,cls in zip(boxes,ids,classes) if cls not in [0]}
                        cameraController.getVehicleTracker('0').updateCouting(vehicles)

                    # Visualize the result on the frame
                    frame = result.plot()
                
                # if shapes is not None: # Adding hitboxes mask to frame
                #     mask = shapes.astype(bool)
                #     frame[mask] = cv2.addWeighted(frame, 0.3, shapes, 1 - 0.3, 0)[mask]
                cv2.putText(frame, status_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if video_state == "Preset Set" else (0, 0, 255), 2)
                if cameraController:
                    phaseData = cameraController.getDataFromTracking('0')
                    cv2.putText(frame, f"Vehicles In: {cameraController.getVehicleTracker('0').getEnteringCount()} ( {'{:.2f} veic/s'.format(phaseData['VehiclesEnteringRate'])})", (600,60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame, f"Vehicles Out: {cameraController.getVehicleTracker('0').getLeavingCount()} ( {'{:.2f} veic/s'.format(phaseData['VehiclesLeavingRate'])})", (600,90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame, f"Vehicles Queued: {phaseData['QueuedVehicles']}", (600,120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame, f"Pedestrians In: {cameraController.getPedestrianTracker('0').getEnteringCount()} ({'{:.2f} veic/s'.format(phaseData['PedestriansEnteringRate'])})", (20,60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame, f"Pedestrians Out: {cameraController.getPedestrianTracker('0').getLeavingCount()} ({'{:.2f} veic/s'.format(phaseData['PedestriansLeavingRate'])})", (20,90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame, f"Pedestrians Queued: {phaseData['QueuedPedestrians']}", (20,120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame, f"{cameraController.getVehicleTracker('0').getEnteringList()}", (20,150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # Display the annotated frame
                cv2.imshow("Video", frame)
                # Recording frame (if setted)
                if export: output.write(frame)

                
                # Break the loop if 'q' is pressed
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        # Release the video capture object and close the display window
        cap.release()
        if export: output.release()
        cv2.destroyAllWindows()
        log.write('######################################\n\n')
    
    log.close() # close log file


if __name__ == '__main__':

    # hitbox data for each preset
    with open('video_detection/data/presetsHitbox.json', 'r') as f:
        data = json.load(f, object_hook=lambda d: Hitbox(**d))
        hitboxes = {h.preset : h for h in data}

    trackingSimulation(hitboxes, [simulationParams], True)
