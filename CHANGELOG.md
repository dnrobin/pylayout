# Changelog
All changes to the pylayout codebase are documented in this file.

## [0.0.1] - 2019-07-10
### Added
- initial release with wrapper functions around gdspy
- sample waveguide generation feature with automatic bends
- (alpha) simple heuristic based autorouter

## [0.4.0] - 2020-03-18
### Changed
- most of the codebase has undergone significant modifications
### Added
- complete framework that wraps around gdspy v1.5.2
- the framework includes: math, geometry, process specification, component hierarchy and routing
- the component builder model is helpful for writing generic component scripts with user defined values
- the framework now includes a minimal Qt5 viewer

## [1.0.0] - 2021-02-22
## Changed
- the codebase has undergone significant modifications to fix many issues primarely with the layout architecture
## Removed
## Added
- math functions for computational geometry
- A-star heuristic for routing