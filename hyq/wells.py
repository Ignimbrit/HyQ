class well:
    '''
    A class to represent a pumping well

    Attributes
    __________
    ID: str
        A string used to identify the well
    x: float
        easting coordinate of the well position in a cartesian grid
    y: float
        northing coordinate of the well position in a cartesian grid
    Q: float
        Pumping rate of the well [m³/s]
    '''
    def __init__(self, ID, x, y, Q):

        self.ID = ID
        self.x = x
        self.y = y
        self.Q = Q