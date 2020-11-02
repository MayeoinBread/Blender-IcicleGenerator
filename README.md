# Blender-IcicleGenerator_2-80
Icicle Generator updated for Blender 2.80

Some improvements over 2.7x version.

* "Generate" button, set up parameters before generating the icicles
* Option to work on whole mesh, or selected edges only
* Option to select the cap type for the cones
* Code refactoring to improve performance


## Installation
* Download the code as .ZIP file from GitHub (Green Code button -> Download ZIP)
* In Blender, open Preferences (Edit -> Preferences)
* Select the Add-ons tab on the left column
* Click the Install button and select the downloaded .ZIP file

## Usage
* Script can only be used with Mesh objects in Edit mode
* Select the edges you want to add icicles to
* Icicles can be added in two ways:
  * Select Generate Icicles from the search menu. This will generate icicles with default settings
  * An Icicle Generator tab should be visible in the right side-bar (Shortcut: N, in Edit Mode only). Settings can be adjusted before clicking Generate to create the icicles.
* In both cases, the icicles must be deleted if you need to regenerate them

## Upcoming Features
* Replace existing icicles when regenerating without need to manually delete old iterations
* Helpers in 3D view to show min/max parameters
