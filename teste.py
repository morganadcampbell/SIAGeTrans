import cv2
import math
import time
import numpy as np
from ultralytics import YOLO
# import easyocr
# reader = easyocr.Reader(['pt'])


# parameters
UPDATE_RATE = 1 #frames

# hitbox data for each preset
DEPARTING_FIRST_POINT = [[ (200,  350),   (950,  390)], 
                         [ (10,   170),   (300,  190)]]
DEPARTING_LAST_POINT =  [[ (200,  400),   (950,  440)], 
                         [ (10,   220),   (300,  200)]]
ARRIVING_FIRST_POINT =  [[ (1090, 250),   (1278, 230)], 
                         [ (750,  230),   (1140, 240)]]
ARRIVING_LAST_POINT =   [[ (1090, 200),   (1278, 220)], 
                         [ (750,  210),   (1140, 220)]]
PEDESTRIAN_BOXES = [[[(910, 400), (1170, 715)], [(0,    550), (140,  300)]], 
                    [[(40,  300), (400,  245)], [(1150, 280), (1270, 500)]]]



# based on https://github.com/rajith-ravikumar-gwu/people_counter/blob/main/tracker.py
class ObjectsTracker:
    def __init__(self):
        self.distanceThreshold = 35
        self.objects_center = {}
        self.objects_count = 0
    def updateTracking(self, objects_boxes):
        objects_boxes_ids = []
        for box in objects_boxes: # for each object detected
            x1, y1, x2, y2, conf, clsname = box
            cx, cy = (x1 + (x2 - x1)//2), (y1 + (y2 - y1)//2) # draw its boudingbox
            same_object_detected = False
            for id, pt in self.objects_center.items(): # test proximity to each previously detected objects
                if math.hypot(cx - pt[0], cy - pt[1]) < self.distanceThreshold: # calculating euclidean distance
                    self.objects_center[id] = (cx, cy)
                    objects_boxes_ids.append([x1, y1, x2, y2, id, conf, clsname])
                    same_object_detected = True
                    break
            if not same_object_detected:
                self.objects_center[self.objects_count] = (cx, cy)
                objects_boxes_ids.append([x1, y1, x2, y2, self.objects_count, conf, clsname])
                self.objects_count += 1
        self.objects_center = {obj_box_id[4]: self.objects_center[obj_box_id[4]] for obj_box_id in objects_boxes_ids}
        return objects_boxes_ids


# model will be downloaded on the first run
model = YOLO('video_detection/yolo_model/yolov8n.pt')
# loading video sample
video = cv2.VideoCapture("video_detection/data/video_30sec.mp4")
# instantiating tracker
tracker = ObjectsTracker()

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
detected_object_data,detected_object = [],[]

# defining areas
area1 = sum(list(map(list,DEPARTING_FIRST_POINT[currentpreset - 1])),[])
area2 = sum(list(map(list,DEPARTING_LAST_POINT[currentpreset - 1])),[])
departing = {}
counter1 = []

if video.isOpened():
    while True:
        count += 1
        framecount += 1
        ret, frame = video.read()
        if not ret: break

        # # drawing hitboxes
        cv2.rectangle(frame, DEPARTING_FIRST_POINT[currentpreset - 1][0], DEPARTING_FIRST_POINT[currentpreset - 1][1], (255,0,0), 2)
        cv2.putText(frame, "area1", DEPARTING_FIRST_POINT[currentpreset - 1][0], cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 1)
        cv2.rectangle(frame, DEPARTING_LAST_POINT[currentpreset - 1][0], DEPARTING_LAST_POINT[currentpreset - 1][1], (255,0,0), 2)
        cv2.putText(frame, "area2", DEPARTING_LAST_POINT[currentpreset - 1][0], cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 1)
        # cv2.rectangle(frame, ARRIVING_FIRST_POINT[currentpreset - 1][0], ARRIVING_FIRST_POINT[currentpreset - 1][1], (255,0,0), 2)
        # cv2.rectangle(frame, ARRIVING_LAST_POINT[currentpreset - 1][0], ARRIVING_LAST_POINT[currentpreset - 1][1], (255,0,0), 2)
        # for b in PEDESTRIAN_BOXES[currentpreset - 1]:
        #     cv2.rectangle(frame, b[0], b[1], (0,0,255), 2)
        cv2.putText(frame, "Count: " + str(len(counter1)), (50,50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2)

        # updating object detection
        if count > UPDATE_RATE:
            detected_object.clear()
            detected_object_data.clear()
            count = 0
            results = model(frame)

            # listing detected objects
            for r in results: 
                for box in r.boxes:
                    coordinates = box.xyxy.tolist()[0]
                    x1, y1, x2, y2 = int(coordinates[0]), int(coordinates[1]), int(coordinates[2]), int(coordinates[3])
                    conf = round(float(box.conf[0]),2) # Confidence score
                    clsname = model.names.get(int(box.cls[0]))
                    detected_object.append([x1, y1, x2, y2, conf, clsname])
            # endfor (listing detected objects)
            detected_object_data = tracker.updateTracking(detected_object)

            # check objects in departing hitboxes
            for objbox in detected_object_data:
                x1, y1, x2, y2, obj_id, conf, clsname = objbox
                cx,cy = x1 + (x2-x1)//2, y1 + (y2-y1)//2 # get center point
                cv2.putText(frame, ".", (cx,cy), cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 255, 0), 4)
                if area1[0] <= cx <= area1[2] and area1[1] <= cy <= area1[3]: departing[obj_id] = (cx,cy)
                if obj_id in departing and obj_id not in counter1 and area2[0] <= cx <= area2[2] and area2[1] <= cy <= area2[3]:
                    counter1.append(obj_id)
                if obj_id in counter1:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, "ID" + str(obj_id) + "-" + clsname + "-" + str(conf), (obj[0], obj[1] + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 1)
            # endfor (check objects in departing hitboxes)
        # endif (updating object detection)

        # drawing objects boxes from results
        for obj in detected_object_data:
            if obj[4] >= 0.7:
                cv2.rectangle(frame, (obj[0], obj[1]), (obj[2], obj[3]), (0, 255, 0), 2)
                cv2.putText(frame, "ID" + str(obj[4]) + "-" + obj[6] + "-" + str(obj[5]), (obj[0], obj[1] + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 1)
        # endfor (drawing objects boxes from results)

        #update frame
        cv2.imshow("video", frame)
        # out.write(frame)


        # if framecount > 300: break
        if cv2.waitKey(1) == ord('q'): 
            break

    # endwhile
    video.release()
    # out.release()
    cv2.destroyAllWindows()
else: raise(Exception("Video could not be opened"))
















# image = cv2.imread("video_detection/data/preset1.png") # read image
# image_size = list(map(lambda x : x//3, image.shape[:2]))[::-1] # calculating new size
# image_resized = cv2.resize(image, image_size) # resize to 1/3
# cropped_image = image_resized[image_size[1]//5*4:image_size[1]-1,       # cropping to preset place
#                               image_size[0]//8*4:image_size[0]//8*6]    # (4/5 to 5/5) height and (4/8 to 6/8) width


# result = reader.readtext(cropped_image)
# complete_text = "".join(list(map(lambda x : x[1], result)))
# print(complete_text)

# for detection in result:
#     top_left = tuple(map(int, detection[0][0]))
#     bottom_right = tuple(map(int, detection[0][2]))
#     text = detection[1]

#     cropped_image = cv2.rectangle(cropped_image, top_left, bottom_right, (0,255,0), 3)
#     print(text)
    
#     while True:
#         cv2.imshow("image", cropped_image)
#         if cv2.waitKey() == ord('q'): break

# #Mouse callback function
# def mouse_callback(event, x, y, flags, param):
#     if event == cv2.EVENT_RBUTTONDBLCLK or event == cv2.EVENT_LBUTTONDBLCLK or event == cv2.EVENT_RBUTTONDOWN:
#         print(f"Mouse clicked to: ({x}, {y})") 
#     pass
    
# video = cv2.VideoCapture("video_detection/data/video_1min.mp4")
# count = 0
# preset = 0

# if video.isOpened():
#     while True:
#         count += 1
#         ret, frame = video.read()
#         if not ret: break
        
#         if preset == 1:
#             cv2.rectangle(frame, (1091, 388), (705, 240), (0,255,0), 2)
#             cv2.rectangle(frame, (254, 222), (196, 340), (255,0,0), 2)

#         cv2.imshow("video", frame)
#         cv2.setMouseCallback("video", mouse_callback)

#         if count == 50:
#             image_size = frame.shape[:2][::-1] # (y,x) -> (x,y)
#             cropped_frame = frame[image_size[1]//5*4:image_size[1]-1,       # cropping to preset place
#                                       image_size[0]//8*4:image_size[0]//8*6]    # (4/5 to 5/5) height and (4/8 to 6/8) widt
#             result = reader.readtext(cropped_frame)
#             complete_text = "".join(list(map(lambda x : x[1], result)))
            
#             if len(complete_text) > 6 and "Preset" in complete_text:
#                 print(complete_text)
#                 if "Preset2" in complete_text: preset = 1
#                 else: preset = 0
#             count = 0

#         if cv2.waitKey(1) == ord('q'): 
#             break

# else: raise(Exception("Video could not be opened"))


# # # image = cv2.imread("video_detection/data/preset1.png") # read image
# # # image_size = list(map(lambda x : x//3, image.shape[:2]))[::-1] # calculating new size
# # # image_resized = cv2.resize(image, image_size) # resize to 1/3
# # # cv2.rectangle(image_resized, (594,342), (754,473), (0,255,0), 2)
# # # cv2.rectangle(image_resized, (82,310), (604,337), (255,0,0), 2)
# # # while True:
# # #     cv2.imshow("image", image_resized)
# # #     cv2.setMouseCallback("image", mouse_callback)
# # #     if cv2.waitKey() == ord('q'): break