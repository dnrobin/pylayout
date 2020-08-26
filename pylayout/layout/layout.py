from ..core import Transforms

class Reference(Transforms):
    def __init__(self, instance, **kwargs):
        self.name = instance.name
        self.instance = instance


class Layout:
    """Circuit-level description of device interconnections

    Layout is a container for placed components (component instances on a floor
    plan) with defined routes (optical or electrical connections) that generate
    a circuit layout. It is possible to place children layouts and thus create
    a hierarchy spanning the fundamental building blocks to the complete system.

    Arguments
    ---------
    name : string, a unique name used to reference this layout
    """
    def __init__(self, name, unit=1e-6, precision=1e-9):
        self.name = name
        self.unit = unit
        self.prec = precision

        self.ports = []
        self.items = {}

        # self.lib = ComponentLibrary()
        self.lib = []

    def place(self, name, item, origin=(0,0), rotation=0, scale=1, flipH=False):

        if item == self:
            raise AttributeError("Trying to place layout object in itself!")

        if name in self.items.keys():
            raise ValueError(f"An item with the name '{name}' already exists in layout.")

        if isinstance(item, Component):
            if not item in self.lib:
                self.lib.append(item)

        self.items[name] = Reference(item, origin=origin, rotation=rotation, scale=scale)

    def to_gds(self, unit=1e-6, precision=1e-9, _global={}):
        """ Convert this layout to gdspy Cell object """
        from gdspy import Cell, CellReference

        # merge with parent lib
        for c in self.lib:
            if not c.name in _global.keys():
                _global[c.name] = (c, c.to_gds(unit, precision))
            
            # same name, different object?
            if not _global[c.name][0] == c:
                raise AssertionError(f"A different component with the name '{c.name}' already exists in the layout!")

        # add cell references
        cell = Cell(self.name, exclude_from_current=True)
        for name, item in self.items.items():
            if isinstance(item.instance, Layout):
                if not item.name in _global.keys():
                    _global[item.name] = (item.instance, item.instance.to_gds(unit, precision, _global))
            
            cell.add(CellReference(_global[item.name][1], item.origin, item.rotation, item.scale, item.flipped))

        return cell

    def write(self, filename):
        """ Write layout to GDSII """
        from os.path import realpath
        from gdspy import GdsLibrary

        lib = GdsLibrary(self.name, unit=self.unit, precision=self.prec)
        lib.add(
            self.to_gds(self.unit, self.prec), overwrite_duplicate=False
        )

        with open(realpath(filename), 'wb') as outfile:
            lib.write_gds(outfile)