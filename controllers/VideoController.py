import cv2
import pickle
import numpy as np
from models.client import Client
import configs.configs as configs
from controllers.ObjectTracker import *
from video_detection.auxiliar.PresetRecognition import *
from models.DataProvisionStructure import *
from models.Hitbox import *

class DataProvisionClient(Client):
    def __init__(self, regionId : int, intersectionId: int):
        clientConfigs = configs.mqtt_broker_videocontroller_client_config
        clientConfigs['client_name'] = f"{clientConfigs.get('client_name')}_{intersectionId}" # subscribe as 'VideoController_<id>'
        clientConfigs['publisher_topic'] = f"/{regionId}{clientConfigs.get('publisher_topic')}" # publish to topic '/<region code>/dataProvision'
        super().__init__(**clientConfigs)

class VideoController:
    def __init__(self, vehiclesTrackersPerPhase : dict[VehicleTracker], pedestrianTrackersPerPhase : dict[PedestrianTracker],
                 regionId : int = None, intersectionId: int = None,
                 username : str = None, password : str = None, ca_certificate : str = None, client_certificate : str = None, client_key : str = None):
        self.__vehiclesTrackersPerPhase = vehiclesTrackersPerPhase
        self.__pedestrianTrackersPerPhase = pedestrianTrackersPerPhase
        self.__phasesIds = vehiclesTrackersPerPhase.keys()
        self.__regionId = regionId
        self.__intersectionId = intersectionId
        self.__username = username
        self.__password = password
        self.__ca_certificate = ca_certificate
        self.__client_certificate = client_certificate
        self.__client_key = client_key

    def getVehicleTracker(self, phaseId) -> VehicleTracker: return self.__vehiclesTrackersPerPhase[phaseId]
    def getPedestrianTracker(self, phaseId) -> PedestrianTracker: return self.__pedestrianTrackersPerPhase[phaseId]
                
    def provideData(self):
        # publish metrics obtained from video
        dataPerPhase = []
        for phaseId in self.__phasesIds: dataPerPhase.append(self.getDataFromTracking(phaseId))
        dataProvisionClient = DataProvisionClient(self.__regionId, self.__intersectionId)
        dataProvisionClient.setSecureConnection(self.__username,self.__password,self.__ca_certificate,self.__client_certificate,self.__client_key)
        dataProvisionClient.connectToBroker()
        pickled_data = pickle.dumps(dataPerPhase)
        dataProvisionClient.publish(pickled_data)
        dataProvisionClient.disconnectFromBroker()

    def getDataFromTracking(self, phaseId):
        d = dict()
        d['PhaseId'] = phaseId
        d['QueuedVehicles'] = self.__vehiclesTrackersPerPhase[phaseId].getQueueCount()
        d['VehiclesEnteringRate'] = self.__vehiclesTrackersPerPhase[phaseId].getQueueEnteringRate()
        d['VehiclesLeavingRate'] = self.__vehiclesTrackersPerPhase[phaseId].getQueueLeavingRate()
        d['EmergencyVehicles'] = self.__vehiclesTrackersPerPhase[phaseId].getQueuedEmergencyVehicles()
        d['QueuedPedestrians'] = self.__pedestrianTrackersPerPhase[phaseId].getQueueCount()
        d['PedestriansEnteringRate'] = self.__pedestrianTrackersPerPhase[phaseId].getQueueEnteringRate()
        d['PedestriansLeavingRate'] = self.__pedestrianTrackersPerPhase[phaseId].getQueueLeavingRate()
        return DataProvisionStructure(**d)

    @staticmethod
    def drawHitboxMask(frame, hitbox):
        shapes = np.zeros_like(frame, np.uint8) # Initialize blank mask image of same dimensions for drawing the shapes
        cv2.fillPoly(shapes, [np.array(hitbox.laneArea, np.int32)], (0, 0, 255))
        for p in hitbox.sidewalkArea:
            cv2.fillPoly(shapes, [np.array(p, np.int32)], (0, 255, 0))
        return shapes
    
    @staticmethod
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

