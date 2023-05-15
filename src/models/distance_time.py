class DistanceTime:
    def __init__(self, walking_distance, walking_time, driving_distance, driving_time, transit_distance, transit_time, biking_distance, biking_time):
        """
        Object for storing distance and time data of all modes of transportation.
        Time in minutes, distance in kilometers.
        Variables already have unit suffixes.
        """
        self.walking_distance = walking_distance
        self.walking_time = walking_time
        self.driving_distance = driving_distance
        self.driving_time = driving_time
        self.transit_distance = transit_distance
        self.transit_time = transit_time
        self.biking_distance = biking_distance
        self.biking_time = biking_time
        
    @classmethod
    def with_zero_values(cls):
        return cls(0, 0, 0, 0, 0, 0, 0, 0)
