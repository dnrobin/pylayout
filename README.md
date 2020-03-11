# pylayout

pylayout is a small library to aid in the design of silicon photonics integrated circuits adding a layer of logic over the awesome `gdspy` library. It stems from the needs and desires of my research group in wanting an open source framework that accelarates development. The philosophy is greatly inspired by KLayout's scripted macro approach but without the IDE constraint. The library features cricuit-level design features like component placement and routing, but also component-level design to engineer the building blocks.

The package also features a simple yet sophisticated Qt5 viewer that can be invoked from script just like a matplotlib plot window but with interactive control over the visible layers and component hierarchy to provide visual feedback as design progresses. It can be run in standalone watch mode where the view is updated upon changes to the layout script file.
