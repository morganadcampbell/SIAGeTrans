class Hitbox:
    def __init__(self, preset, queuedArea : list[list], trackedOut : list[list], trackedIn : list[list], trackedPedestrians : list[list[list]]):
        self.preset = preset
        self.queuedArea = queuedArea
        self.trackedOut = trackedOut
        self.trackedIn = trackedIn
        self.trackedPedestrians = trackedPedestrians