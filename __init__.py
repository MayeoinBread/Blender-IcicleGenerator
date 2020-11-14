bl_info = {
    "name":"Icicle Generator",
    "author":"Eoin Brennan (Mayeoin Bread)",
    "version":(2,6),
    "blender":(2,90,0),
    "location":"3D View > Tools",
    "description":"Add icicles of varying widths & heights to selected non-vertical edges",
    "warning":"",
    "wiki_url":"",
    "tracker_url":"",
    "category":"Add Mesh"
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
from . ig_panel import OBJECT_PT_IciclePanel
from . ig_gen_op import WM_OT_GenIcicle
from . draw_op import OT_Draw_Preview

# Properties class to hold required parameters
class IcicleProperties(PropertyGroup):

    def tgl_update_fnc(self, context):
        if self.preview_btn_tgl:
            bpy.ops.wm.icicle_preview('INVOKE_DEFAULT')
        return

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

    direction: EnumProperty(
        name='Points',
        description='Set whether icicles point up or down',
        items=[
            ('Up', 'Up', 'Icicles point upwards'),
            ('Down', 'Down', 'Icicles point downwards (default)')
        ],
        default='Down'
    )

    preview_btn_tgl: BoolProperty(
        name='PreviewTgl',
        default=False,
        update=tgl_update_fnc,
        description='Toggle preview of max/min dimensions in 3D view'
    )

classes = [MyProperties, OBJECT_PT_CustomPanel, OT_Draw_Preview, WM_OT_GenIcicle]
# classes = [MyProperties, OBJECT_PT_CustomPanel, WM_OT_GenIcicle]

# Register/unregister classes
def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.icicle_properties = PointerProperty(type=IcicleProperties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.icicle_properties
