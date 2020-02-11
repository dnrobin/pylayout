# pylayout

pylayout is a collection of scripts to aid in silicon photonics design with the `scripted layout` philosophy as opposed to the CAD approach. It is greatly inspired by KLayout's python macros, but without the constraints of the editor and uses *gdspy* as the engine which allows high-level representations and a hierarchical design approach that can then be converted to simple polygons and exported with industry standard GDSII file format. The package also comes with a simple yet sophisticated Qt5 viewer that can be invoked from script just like a matplotlib plot window but with interactive control over the visible layers and components to provide visual feedback as design progresses.
