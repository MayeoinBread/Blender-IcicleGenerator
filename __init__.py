bl_info = {"name":"Icicle Generator",
           "author":"Eoin Brennan (Mayeoin Bread)",
           "version":(2,5),
           "blender":(2,80,0),
           "location":"3D View > Tools",
           "description":"Adds a linear string of icicles of different sizes",
           "warning":"",
           "wiki_url":"",
           "tracker_url":"",
           "category":"Development"
           }

import bpy

from bpy.props import (
    BoolProperty,
    FloatProperty,
    IntProperty,
    EnumProperty,
    PointerProperty
)

from bpy.types import PropertyGroup

# import all teh ops and stuff
from . ig_panel import OBJECT_PT_CustomPanel
from . ig_gen_op import WM_OT_GenIcicle
# from . draw_op import OT_draw_operator

# Properties class to hold required parameters
class MyProperties(PropertyGroup):
    max_rad: FloatProperty(
        name='Max Radius',
        description='Maximum radius of a cone',
        default=0.15,
        min=0.01,
        max=1.0,
        unit='LENGTH'
    )

    min_rad: FloatProperty(
        name='Min Radius',
        description='Minimum radius of a cone',
        default=0.025,
        min=0.01,
        max=1.0,
        unit='LENGTH'
    )

    max_depth: FloatProperty(
        name='Max Depth',
        description='Maximum depth (height) of a cone',
        default=2.0,
        min=0.0,
        max=2.0,
        unit='LENGTH'
    )

    min_depth: FloatProperty(
        name='Min Depth',
        description='Minimum depth (height) of a cone',
        default=1.5,
        min=0.0,
        max=2.0,
        unit='LENGTH'
    )

    num_verts: IntProperty(
        name='Vertices',
        description='Number of vertices at base of cone',
        default=8,
        min=3,
        max=24
    )

    subdivs: IntProperty(
        name='Subdivides',
        description='Max number of kinks on a cone',
        default=3,
        min=0,
        max=8
    )

    max_its: IntProperty(
        name='Iterations',
        description='Number of iterations before giving up, prevents freezing/crashing',
        default=50,
        min=1,
        max=100
    )

    reselect_base: BoolProperty(
        name='Reselect base mesh',
        description='Reselect the base mesh after adding icicles',
        default=True
    )

    on_selected_edges: BoolProperty(
        name='Only add to selected edges',
        description='Add icicles to selected edges only. Otherwise, applied to all edges in mesh',
        default=True
    )

    add_cap: EnumProperty(
        name='Fill',
        description='Fill the icicle cone base',
        items=[
            ('NGON', 'Ngon', 'Fill with Ngons'),
            ('NOTHING', 'None', 'Do not fill'),
            ('TRIFAN', 'Triangle fan', 'Fill with triangles')
        ],
        default='NGON'
    )

#classes = [MyProperties, OBJECT_PT_CustomPanel, OT_draw_operator, WM_OT_GenIcicle]
classes = [MyProperties, OBJECT_PT_CustomPanel, WM_OT_GenIcicle]


# Register/unregister classes
def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.my_props = PointerProperty(type=MyProperties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.Scene.my_props
