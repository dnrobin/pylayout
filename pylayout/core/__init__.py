from pylayout.math import Vector, Transform, snap

class Transforms:
    """Provides a local-to-parent transform for layout objects
    
    Children inherit the property _local which is a transform instance 
    and also inherit a set of useful methods for local transformations.
    """
    def __new__(cls, *args, **kwargs):

        kv = {}
        for key in Transform.__init__.__code__.co_varnames:
            if key in kwargs:
                kv[key] = kwargs[key]
                del kwargs[key]

        inst = object.__new__(cls)
        inst.__local = Transform(**kv)

        return inst

    def setTransform(self, scale=1,  rotation=0, translation=(0,0)):
        self.__local.setTransform(scale, rotation, translation)
    
    def transform(self, xy, unit=1e-6, precision=1e-9):
        """ apply transform to a set of points and return the result """
        # TODO: consider not snapping at this stage!
        return [Vector(p).snap(precision/unit) for p in self.__local.apply(xy)]

    def set_origin(self, x, y=None):
        """ change local coordinate system origin """
        self._local.translation = -Vector(x, y)

    def reset_transformation(self):
        """ reset transformation to identity """
        self._local.reset()
    
    @property
    def origin(self):
        return self.__local.origin

    @property
    def translation(self):
        return self.__local.translate

    @property
    def rotation(self):
        return self.__local.rotation
    
    @property
    def scale(self):
        return self.__local.scale

    @property
    def scaleX(self):
        return self.__local.scaleX

    @property
    def scaleY(self):
        return self.__local.scaleY

    @translation.setter
    def translation(self,value):
        self.__local.translation = value

    @rotation.setter
    def rotation(self,value):
        self.__local.rotation = value

    @scale.setter
    def scale(self,value):
        self.__local.scale = value

    @scale.setter
    def scaleX(self,value):
        self.__local.scaleX = value

    @scale.setter
    def scaleY(self,value):
        self.__local.scaleY = value

    @property
    def ax(self):
        return self.__local.ax

    @property
    def ay(self):
        return self.__local.ay

    @property
    def forward(self):
        return self.__local.forward

    @property
    def left(self):
        return self.__local.left

    @property
    def right(self):
        return self.__local.right

    @property
    def back(self):
        return self.__local.back

    def scale(self, scale):
        """ apply scaling factor """
        self.__local.scale(scale)

    def rotate(self, angle):
        """ apply rotation by angle in *degrees* """
        self.__local.rotate(angle)

    def translate(self, d, y=False):
        """ apply translation """
        self.__local.translate(d, y)

    def flipV(self):
        """ reflect y-coordinate (mutates the transform) """
        self.__local.flipV()

    def flipH(self):
        """ reflect x-coordinate (mutates the transform) """
        self.__local.flipH()

    def reflect(self):
        """ reflect off the diagonal (mutates the transform) """
        self.__local.reflect()