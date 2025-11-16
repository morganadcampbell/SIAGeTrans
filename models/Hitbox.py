class Hitbox:
    def __init__(self, preset, laneArea : list[list], sidewalkArea : list[list[list]]):
        self.preset = preset
        self.laneArea = laneArea
        self.sidewalkArea = sidewalkArea