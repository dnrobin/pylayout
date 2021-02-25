

class Pin:
    __slots__ = ('name', 'position', 'direction', 'width')
    def __init__(self, name, position=(0,0), direction='e', width=1.0):
        self.name = name
        self.position = position
        self.direction = direction
        self.width = width

