import shapely.geometry as geometry

# lib should specify: dbu, precision, max points (def. 8192)
# all point data must be rounded to integer multiples of dbu
# all polygons must be simple polygons with no intesections
# all paths must never intersect
# all curves must be interpolated over discrete points
# all geometry is constructive in nature: step-by-step creation of polygons where operations are performed on previous step as a whole.

from pylayout.math import Transforms


class Shape(Transforms):
    def __init__(self, unit=1, precision=1e-9):
        super(Shape, self).__init__()

        self.__xy = []      # fundamental set of points exported by this shape

    def shape_type(self):
        ''' returns a string specifying the shape type '''
        pass

    def coords(self):
        ''' extract the x, y transformed coordinates as integer multiples of dbu '''
        pass

    def bounds(self):
        ''' returns [xmin,ymin,xmax,ymax] bounds of the shape 

            Points have zero bounds, everything else defines some bounds.
        '''
        pass

    def length(self):
        ''' returns the length of the shape

            Points have zero length, lines have conventional length: length(p2 - p1),
            paths have a length given by the sum of all straight segment lengths,
            polygons have length equal to their perimeter (including inner holes if any).
        '''
        pass

    def area(self):
        ''' returns the total area covered by the shape

            Points have zero area, lines and paths have zero area, polygons have an area.
        '''
        pass

    def center(self):
        pass

    def inside(self):
        pass

    def distance(self):
        pass


class Point():
    def __init__(self, x, y):
        super(Point, self).__init__()

    def shape_type(self):
        return 'Point'

    def bounds(self):
        xy = super(Point, self).__xy[0]
        return [xy[0], xy[1], xy[0], xy[1]]

    def length(self):
        return 0

    def area(self):
        return 0


class Line():
    def __init__(self, p1, p2):
        super(Point, self).__init__()

    def shape_type(self):
        return 'Line'

    def bounds(self):
        p1 = super(Point, self).__xy[0]
        p2 = super(Point, self).__xy[1]

        return [min(p1[0], p2[0]), min(p1[1], p2[1]), max(p1[0], p2[0]), max(p1[1], p2[1])]

    def length(self):
        return sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def area(self):
        return 0
