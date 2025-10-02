import copy
import cv2
import time
import numpy as np

def getHitBoxPolygonFromVideo(video : str):
    # p = pause
    # f = finish
    # u = undo
    # q = quit
    hitboxCoordinates = []
    update = [False]
    STOPPED = False

    def mouse_callback(event, x, y, flags, param):
        if STOPPED and event == cv2.EVENT_RBUTTONDBLCLK or event == cv2.EVENT_LBUTTONDBLCLK or event == cv2.EVENT_RBUTTONDOWN:
            update[0] = True
            hitboxCoordinates.append((x, y))

    video = cv2.VideoCapture(video)

    if video.isOpened():
        while True:
            ret, frame = video.read()
            original_frame = copy.deepcopy(frame)
            if not ret: break
            cv2.imshow("video", frame)
            cv2.setMouseCallback("video", mouse_callback)
            while STOPPED:
                if cv2.waitKey(1) == ord('u'): #remove last dot
                    if len(hitboxCoordinates) > 0: hitboxCoordinates.pop()
                    frame = copy.deepcopy(original_frame);update[0] = True
                if cv2.waitKey(1) == ord('f'): #finish
                    print("Coordinates:", hitboxCoordinates)
                    hitboxCoordinates.clear()
                    break
                if cv2.waitKey(1) == ord('p'): #unpause
                    STOPPED = False
                    hitboxCoordinates.clear()
                    break
                if update[0]: #update[0] dots
                    frame = copy.deepcopy(original_frame)
                    cv2.putText(frame, "STOPED (p)", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3, cv2.LINE_AA)
                    for i in hitboxCoordinates: # dot all points
                        cv2.putText(frame, ".", i, cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 3, cv2.LINE_AA)
                    if len(hitboxCoordinates) > 2: 
                        shapes = np.zeros_like(frame, np.uint8)
                        cv2.fillPoly(shapes, [np.array(list(map(list, hitboxCoordinates)), np.int32)], (0, 255, 0))
                        alpha = 0.3
                        mask = shapes.astype(bool)
                        frame[mask] = cv2.addWeighted(frame, alpha, shapes, 1 - alpha, 0)[mask]
                    update[0] = False
                cv2.imshow("video", frame)
            #endwhile
            if cv2.waitKey(1) == ord('p'):
                STOPPED = True
            if cv2.waitKey(1) == ord('q'):
                break
    else: 
        raise(Exception("Video could not be opened"))
    video.release()
    cv2.destroyAllWindows()
    return hitboxCoordinates



print(getHitBoxPolygonFromVideo("video_detection/data/video_1min.mp4"))
## Results:
# 1: [(191, 401), (908, 520), (978, 392), (342, 351), 							# Vehicles Departing
# 	(1092, 248), (1278, 235), (1278, 221), (1090, 200), 						# Vehicles Arriving
# 	(1170, 714), (911, 400), (138, 303), (2, 550)], 							# Pedestrians

# 2: [(366, 202), (176, 136), (172, 230), (38, 153), 							# Vehicles Departing
# 	(734, 231), (1138, 241), (818, 206), (1158, 186), 							# Vehicles Arriving
# 	(475, 145), (40, 304), (1152, 218), (1273, 493)] 							# Pedestrians

# 3: [(562, 276), (292, 242), (311, 229), (570, 208), 							# Vehicles Departing
# 	(616, 288), (884, 305), (864, 277), (606, 256), 							# Vehicles Arriving
# 	(907, 231), (1027, 360), (619, 225), (559, 332), (157, 312), (68, 208)] 	# Pedestrians

# 4: [(166, 371), (526, 286), (490, 274), (118, 270), 							# Vehicles Departing
# 	(733, 278), (890, 236), (622, 246), (794, 223), 							# Vehicles Arriving
# 	(157, 286), (5, 562), (641, 197), (933, 387), (1135, 148), (1274, 262)]} 	# Pedestrians

