######################################################
## Contribution of Victor Gomes                     ##
## https://github.com/VictorAGomes/PresetsDetection ##
######################################################

import cv2
import os
import numpy as np

NUM_FEATURES = 1000
GOOD_MATCH_RATIO = 0.80
MIN_GOOD_MATCHES = 10
CONFIRMATION_THRESHOLD = 2
PROCESSING_WIDTH = 640
PROCESSING_HEIGHT = 480
 
def simpleMovementDetection(last_gray_frame, current_gray_frame, conf_threshold=0.15):
    if last_gray_frame is None:
        return False
    diff = cv2.absdiff(last_gray_frame, current_gray_frame)
    _, thresh = cv2.threshold(diff, 40, 255, cv2.THRESH_BINARY)
    ratio = cv2.countNonZero(thresh) / (thresh.shape[0] * thresh.shape[1])
    return ratio > conf_threshold

def analyze_presets_reference(preset_folder):
    orb = cv2.ORB_create(nfeatures=NUM_FEATURES)
    preset_descriptors = {}
    for file_name in os.listdir(preset_folder):
        file_path = os.path.join(preset_folder, file_name)
        preset_name = os.path.splitext(file_name)[0]
        img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            _, descriptors = orb.detectAndCompute(img, None)
            if descriptors is not None:
                preset_descriptors[preset_name] = descriptors
    return orb, preset_descriptors

def identify_preset_features(frame, orb, preset_descriptors):
    _, descriptors_frame = orb.detectAndCompute(frame, None)
    if descriptors_frame is None:
        return None, 0
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    best_preset, max_matches = None, 0
    for preset_name, descriptors in preset_descriptors.items():
        matches = bf.knnMatch(descriptors_frame, descriptors, k=2)
        good_matches = [m for m, n in matches if m.distance < GOOD_MATCH_RATIO * n.distance] if matches else []
        if len(good_matches) > max_matches:
            best_preset, max_matches = preset_name, len(good_matches)
    if max_matches >= MIN_GOOD_MATCHES:
        return best_preset, max_matches
    return None, max_matches
