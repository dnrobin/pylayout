from pylayout.math import Transform, snap

class Transforms:
    def __init__(self):
        self.__transform = Transform()
    
    def transform(self, points, unit=1e-6, precision=1e-9):
        """ apply transform to a set of points and return the result """
        from copy import deepcopy

        xy = deepcopy(points)

        # TODO: apply the transform and snap to unit/precision grid

        for p in xy:
            p[0] += self.__transform.translation[0]
            p[1] += self.__transform.translation[1]

            p[0] = snap(p[0], precision/unit)
            p[1] = snap(p[1], precision/unit)

        return xy

    def translate(self, translation):
        self.__transform.translation[0] += translation[0]
        self.__transform.translation[1] += translation[1]

    def setTransform(self, translation=(0,0), rotation=0, scale=1, flipH=False):
        self.__transform.setTransform(translation, rotation, scale, flipH)

    @property
    def origin(self):
        return self.__transform.translation

    @property
    def rotation(self):
        return self.__transform.rotation

    @property
    def scale(self):
        return self.__transform.scale

    @property
    def flipped(self):
        return self.__transform.flipH