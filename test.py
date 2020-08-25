#!/usr/local/bin/python3
from pylayout.shape.helper import Circle, Rect
from pylayout.layout import *
from pylayout.math import *

print(Vector(3,4).length)

# square = Rect((-100,100),(100,100))

# pad = Component("pad0")
# pad.insert(6,0,square)

# c1 = Component("comp0")
# c1.insert(1,0,Circle((100,100), 200))
# c1.insert(2,0,Circle((0,0), 100))

# ly0 = Layout("layout0")
# ly0.place("pad", pad, (0,0))
# ly0.place("left", c1, (100,300))
# ly0.place("right", c1, (-500,-100))

# ly1 = Layout("layout1")
# ly1.place("pad", pad, (100,100))
# ly1.place("middle", c1, (0,0))

# top = Layout("top")
# top.place("device1", ly0, (-1000,100))
# top.place("device2", ly1, (100,1000))
# top.place("device2_copy", ly1, (5000,5000))

# c1.insert(2,0,Circle((10,10),200))

# top.write("test.gds")