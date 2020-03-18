from pylayout.math import Transform, Transformed, AABB, degrees, radians
from pylayout.utils import isnumeric, direction_angle, unique_name_for
from pylayout.builder import ComponentBuilder
from pylayout.process import ProcessLayer, DesignRules
from pylayout.routing import Port, Connection
from pylayout.shapes import SimplePolygon, Path, FlexPath, RobustPath, Text

import gdspy

import copy
import inspect

class Component:
    """ Combines a GDSII cell with a dictionary of ports for routing

    Compoments are the building blocks of circuit layouts and are composed of shape primitives
    like simple polygons, paths and text labels attached to process layers. They should always 
    define art least one I/O port for routing if they are to be used in circuits.
    """
    def __init__(self, cell: gdspy.Cell, ports=dict()):
        assert isinstance(cell, gdspy.Cell)
        self.cell = cell
        self.ports = ports
    
    def get_bounds(self):
        return AABB(self.cell.get_bounding_box())


class ComponentLibrary:
    def __init__(self, filename=None, unit=1e-6, precision=1e-9):
        self._unit = unit
        self._precision = precision
        self._components = dict()

        if not filename is None:
            self.import_components(filename)

    @property
    def unit(self): return self._unit

    @property
    def precision(self): return self._precision

    def get_component(self, name):
        if name in self._components:
            return self._components[name]
        return None

    def __setitem__(self, key, value):
        if not isinstance(value, Component):
            raise ValueError("Cannot set item '%s' with value that is not a component!" % key)
        self._components[key] = value

    def __getitem__(self, key):
        if not key in self._components:
            raise KeyError("Component '%s' not found in library!" % key)
        return self._components[key]

    def __delitem__(self, key):
        if not key in self._components:
            raise KeyError("Component '%s' not found in library!" % key)
        del self._components[key]

    def __iter__(self):
        return iter(self._components)

    def __len__(self):
        return len(self._components)

    def add(self, name, component: Component):
        if not isinstance(component, Component):
            raise ValueError("Invalid argument supplied to add(), must be a component instance!")

        self._components[name] = component

    def import_components(self, filename, name=None):
        """ import components from GDSII file 
        
        input:
            if no name is provided, imports all components found in file
        """
        from os.path import realpath

        filename = realpath(filename)
        with open(filename, 'rb') as infile:
            lib = gdspy.GdsLibrary(unit=self._unit, precision=self._precision)
            lib.read_gds(infile, units='convert')

            if name is None:
                for cell in lib.cells.values():
                    self._components[cell.name] = Component(cell)
            else:
                if not name in lib.cells:
                    raise KeyError("Component '%' not found in GDS file '%s'!")

                self._components[cell.name] = Component(cell)


    def export_components(self, filename, name=None):
        """ export library to GDSII file

        input:
            if no name is provided, exports everything
        """
        from os.path import realpath

        filename = realpath(filename)
        with open(filename, 'wb') as outfile:
            lib = gdspy.GdsLibrary('library', None, self._unit, self._precision)

            if name is None:
                for comp in self._components.values():
                    lib.add(comp.cell, True, False, True)
            else:
                if not name in lib._components:
                    raise KeyError("Missing component '%' cannot be exported!")

                lib.add(self._components[name].cell, True, False, True)
            
            lib.write_gds(outfile)


class PortReference:
    """ Defines a proxy combining a port reference and a transform in the parent layout

    The PortReference references a real Port instance adding a layer of logic like transformations
    which allow generating multiple instances of the same Port over the circuit layout. The instancing is
    done within the parent ComponentReference, ComponentArray or ComponentVariants.
    """

    __slots__ = ("_port", "_local")

    def __init__(self, port: Port, local: Transform):
        self._port = port
        self._local = local

    @property
    def position(self): return self._local.apply(self._port.position)

    @property
    def direction(self): return degrees(self._local.rotation) + self._port.direction

    @property
    def width(self): return self._port.width

    def __repr__(self):
        return "Port %s, width: %s, direction: %s" % (self.position, self.width, self.direction)


class ComponentReference:
    """ Defines a proxy combining a component reference and a transform in the parent layout

    The ComponentReference references a single Component instance adding a layer of logic and control like
    transformations which allows genereting mutliple instances of the same Component over the circuit layout.
    The instancing is done via the place() methods of the layout. The component reference creates port references 
    from the referenced component in order to transform the coordinates of the placed ports in the layout used 
    for routing components together. It is possible to create arrays of references spanning a grid of rows and 
    collumns or event instantiate variations of the component in a side-by-side array (see ComponentArray and
    ComponentVariants).
    """

    __slots__ = ("name", "cell", "ports")

    def __init__(self, name: str, comp: Component, local: Transform):
        self.name = name
        self.cell = gdspy.CellReference(
            comp.cell, 
            local.translation, 
            degrees(local.rotation), 
            local.get_scale(1),
            x_reflection = local.get_scale(0) < 0)

        self.ports = dict()
        for name, port in comp.ports.items():
            self.ports[name] = PortReference(port, local)

    def get_bounds(self):
        return AABB(self.cell.get_bounding_box())
    
    def get_origin(self):
        return self.cell.origin
    
    def get_area(self):
        return self.cell.area()

    def get_port(self, key):
        if isnumeric(key):
            ports = self.ports.value()
            if key < 0 or key >= len(ports):
                raise IndexError('Port index out of range!')
            return ports[key]
        else:
            if key in self.ports:
                return self.ports[key]
            else:
                raise KeyError("Port name '%s' not found on component!" % key)


class ComponentArray:
    """ Defines a proxy array combining a component reference and a transform in the parent layout """

    __slots__ = ("name", "cell", "ports")
        
    def __init__(self, rows, cols, name: str, comp: Component, local: Transform, padding=0):
        assert cols > 0
        assert rows > 0
        self.name = name

        if isnumeric(padding):
            padding = (padding, padding)

        sx, sy = comp.get_bounds().size()
        spacing = (sx + padding[0], sy + padding[1])

        self.cell = gdspy.CellArray(comp.cell, cols, rows, spacing, 
            local.translation, 
            degrees(local.rotation), 
            local.get_scale(1),
            x_reflection = local.get_scale(0) < 0)

        self.ports = list()
        for i in range(rows):
            self.ports.append([])
            for j in range(cols):

                dx, dy = local.apply((j * spacing[0], i * spacing[1]))
                t = Transform(local.get_scale(), local.rotation, (dx, dy))

                self.ports[i].append(dict())
                for name, port in comp.ports.items():
                    self.ports[i][j][name] = PortReference(port, t)

    def get_bounds(self):
        return AABB(self.cell.get_bounding_box())
    
    def get_origin(self):
        return self.cell.origin
    
    def get_area(self):
        return self.cell.area()

    def get_port(self, row, col, key):
        if row >= self.rows or col >= self.cols:
            raise ValueError("row, column out of range for component array of size [%d,%d]" % (self.rows, self.cols))

        if isnumeric(key):
            ports = self.ports[row][col].values()
            if key < 0 or key >= len(ports):
                raise IndexError('Port index out of range!')
            return ports[key]
        else:
            if key in self.ports[row][col]:
                return self.ports[row][col][key]
            else:
                raise KeyError("Port name '%s' not found on component!" % key)


class ComponentVariants:
    # TODO: ######################
    pass


class Layout:
    """ Defines a circuit-level description of components and routes

    The Layout is the parent cell for components and defines placed component references
    and port connections which are later used to generate traces for waveguides or electrical
    connections. It is possible to place sub layouts within a layout and thus build a hierarchy
    of cells from component definitions to device layout to system layout.
    """
    def __init__(self, name, lib=None, unit=1e-6, precision=1e-9):
        """
        input:
            name - str, a allow_duplicates name for this layout
            lib - ComponentLibrary, shared component library or None to create a new one
            unit, precision - number, snap all layout elements to the grid defined by grid=(precision/unit)
        """
        self.cell = gdspy.Cell(name)
        self._name = name
        
        if lib is None:
            lib = ComponentLibrary(unit=unit, precision=precision)

        self._lib = lib
        self._unit = lib.unit
        self._precision = lib.precision

        self._layouts = dict()          # dictionary of placed sub layouts
        self._references = dict()       # dictionary of placed components
        self._connections = list()      # list of connections between ports

    @property
    def components(self): return self._references
    
    @property
    def layouts(self): return self._layouts

    def get_bounds(self):
        return AABB(self.cell.get_bounding_box())

    def place_layout(self, layout, origin=(0,0), orientation='e', scalefactor=1.0, flipV=False, allow_duplicates=False):
        """ insert a layout into this layout at coordinates given by origin 
        
        input:
            layout - Layout, the layout instance to be inserted
            allow_duplicates - bool, if false, allow inserting multiple copies of the same layout generating a allow_duplicates name for them

        output:
            name of the inserted layout (same if allow_duplicates or generated name if a copy)
        """
        self._gdslib.add(layout.cell, True, not allow_duplicates, True)

        if not isinstance(item, Layout):
            raise ValueError('Invalid argument supplied to sub_layout(), must be a Layout instance!')

        if isnumeric(scalefactor):
            scalefactor = (scalefactor, scalefactor)
        if flipV:
            scalefactor[1] = -scalefactor[1]

        if layout._name == self._name:
            raise ValueError("Cannot add sub layout with the same name as this layout!")

        name = layout._name
        if name in self._layouts:
            if not allow_duplicates:
                raise ValueError("A sub layout by the name '%s' already exists in the layout '%'", (name, self._name))
            name = unique_name_for(name, self._layouts)

        self._layouts[name] = layout

        self.cell.add(gdspy.CellReference(layout.cell, 
            origin,
            direction_angle(orientation),
            scalefactor[1],
            x_reflection = scalefactor[0] < 0))

        return name

    def _place(self, name, item, origin=(0,0), orientation='e', scalefactor=1.0, flipV=False, params={}, allow_duplicates=False):

        if name == self._name:
            raise ValueError("Cannot place a component with the same name as the layout name!")
        
        if name in self._references:
            if not allow_duplicates:
                raise ValueError("A component with the name '%s' already exists on the layout!" % name)
            name = unique_name_for(name, self._references)

        if isinstance(item, Component):
            comp = item

        if isinstance(item, str):
            if not item in self._lib:
                raise ValueError("Component name '%s' not found in layout's component library!" % item)
            comp = self._lib[item]

        else:

            if inspect.isclass(item):
                item = item(**params)
            
            if not isinstance(item, ComponentBuilder):
                raise ValueError('Invalid argument supplied to place(), item must be a component instance or a builder!')

            comp = self._builer_to_cell(item)

        local = Transform(
            scalefactor, 
            radians(direction_angle(orientation)), 
            origin, 
            self._unit, 
            self._precision)
        if flipV:
            local.flipV()
        
        return (name, comp, local)

    def place(self, name, item, origin=(0,0), orientation='e', scalefactor=1.0, flipV=False, params={}, allow_duplicates=False):

        (name, comp, local) = self._place(name, item, origin, orientation, scalefactor, flipV, params, allow_duplicates)

        reference = ComponentReference(name, comp, local)
        self.cell.add(reference.cell)
        self._references[name] = reference

        return reference

    def array(self, name, item, rows, cols, padding=0, origin=(0,0), orientation='e', scalefactor=1.0, flipV=False, params={}, allow_duplicates=False):
        
        (name, comp, local) = self._place(name, item, origin, orientation, scalefactor, flipV, params, allow_duplicates)

        reference = ComponentArray(rows, cols, name, comp, local, padding)
        self.cell.add(reference.cell)
        self._references[name] = reference

        return reference

    def _port(self, port):
        if isinstance(port, PortReference):
            return port
        elif isinstance(port, ComponentReference):
            return self.get_port(port.name)
        elif isinstance(port, str):
            return self.get_port(port)
        elif isinstance(port, Component):
            raise ValueError("Cannot route a library component! The component must first be place on the layout.")
        else:
            raise TypeError("Invalid argument type for port in connect(), got %s" % type(port))
    
    def connect(self, port1, port2, bend_radius=1):
        """ connect two ports to create a route 

        input:
            port1, port2 - PortRef, ComponentReference or string of the form '<component_name> ([<row>]) ([<col>]) (.<port_name>)'
            Note: if a ComponentReference is passed, or a component_name alone is given, the function checks to see if the 
            component has only a single port, and if so, uses that one, otherwise raises an error to require more identification.
        """
        _port1 = self._port(port1)
        _port2 = self._port(port2)

        if _port1.width != _port2.width:
            raise ValueError("Cannot connect ports '%s' and '%s' with different width" % (_port1, _port2))

        connection = Connection(_port1, _port2, self._unit, self._precision)
        
        self._connections.append(connection)

        return connection

    def get_component(self, name: str) -> Component:
        """ get placed component by name """
        if not name in self._references:
            raise KeyError("Component '%s' not found in layout '%s'" % (name, self._name))
        return self._references[name]
        
    def get_port(self, identifier: str) -> Port:
        """ get placed component port by name identifier """
        import re

        match = re.fullmatch('(\w+)(?:\[(\d+)\])?(?:\[(\d+)\])?(?:\.(\w+))?', identifier)
        if match is None:
            raise ValueError('Invalid port identifier string!')
        
        groups = match.groups()
        
        comp_name = groups[0]
        if not comp_name in self._references:
            raise KeyError("Component '%s' not found in layout '%s'" % (comp_name, self._name))

        component = self._references[comp_name]

        def _get(port_name, ports: dict):
            if len(ports) == 0:
                raise ValueError("Cannot create connection with component '%s', it has no ports!" % comp_name)

            if port_name is None:
                if len(ports) > 1:
                    raise ValueError("Missing port name for component '%s' with mutliple ports" % comp_name)

                return list(ports.values())[0]
            else:
                if not port_name in ports:
                    raise KeyError("Component '%s' has no port with the name '%s'" % (comp_name, port_name))
            
            return ports[port_name]
        

        if not groups[1] is None:
            index1 = int(groups[1])
            if not groups[2] is None:
                index2 = int(groups[2])

                if not isinstance(component, ComponentArray):
                    raise KeyError("Component '%s' is not an instance of ComponentArray" % comp_name)
                
                if len(component.ports) <= index1:
                    raise KeyError("Row index out of range for component array '%s'" % comp_name)

                if len(component.ports[index1]) <= index2:
                    raise KeyError("Column index out of range for component array '%s'" % comp_name)

                return _get(groups[3], component.ports[index1][index2])
            else:
                if not isinstance(component, ComponentVariants):
                    raise KeyError("Component '%s' is not an instance of ComponentVariants" % comp_name)

                if len(component.ports) < index1:
                    raise KeyError("Item index out of range for variations '%s'" % comp_name)

                return _get(groups[3], component.ports[index1])
        
        if not isinstance(component, ComponentReference):
            if isinstance(component, ComponentVariants):
                raise KeyError("Component '%s' is an instance of ComponentVariants and must be addressed by index" % comp_name)
            elif isinstance(component, ComponentArray):
                raise KeyError("Component '%s' is an instance of ComponentArray and must be addressed by [row][column]" % comp_name)
            else:
                raise KeyError("Unexpected type for component '%s'... Report this error." % comp_name)

        return _get(groups[3], component.ports)

    def _builer_to_cell(self, builder: ComponentBuilder):
        import gdspy

        name = repr(builder)

        if name in self._lib:
            return self._lib[name]

        else:
            cell = gdspy.Cell(name)

            for layer, shape in builder.shapes:
                if isinstance(shape, (SimplePolygon, FlexPath, RobustPath)):
                    cell.add(gdspy.Polygon(shape.get_points(self._unit, self._precision), layer.layer, layer.dtype))
                
                elif isinstance(shape, Path):
                    if shape.gds_path:
                        cell.add(gdspy.FlexPath(
                            shape.get_points(self._unit, self._precision),
                            shape.width,
                            precision=self._precision/self._unit,
                            gdsii_path=True, 
                            layer=layer.layer,
                            datatype=layer.dtype))
                    else:
                        cell.add(gdspy.Polygon(
                            shape.get_points(self._unit, self._precision), 
                            layer.layer, 
                            layer.dtype))

                elif isinstance(shape, Text):
                    if shape.polygonal:
                        cell.add(gdspy.Text(
                            shape.text, 
                            shape.size, 
                            shape.position, 
                            True, 
                            degrees(shape.rotation), 
                            layer.layer, 
                            layer.dtype))
                    else:
                        cell.add(gdspy.Label(
                            shape.text, 
                            shape.position,
                            shape.anchor, 
                            degrees(shape.rotation), 
                            shape.size, 
                            False,
                            layer.layer,
                            layer.dtype))

            c = Component(cell, builder.ports)
            self._lib.add(name, c)
            return c

    def save(self, filename):
        """ export layout to GDSII file """
        from os.path import realpath

        lib = gdspy.GdsLibrary(self._name, unit=self._unit, precision=self._precision)
        lib.add(self.cell, True, False, True)

        filename = realpath(filename)
        with open(filename, 'wb') as outfile:
            lib.write_gds(outfile)