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

import bpy_types
from bpy.types import Panel

class OBJECT_PT_IciclePanel(Panel):
    bl_idname = 'OBJECT_PT_icicle_panel'
    bl_label = 'Icicle Generator'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Icicle Generator'
    bl_context = 'mesh_edit'

    @classmethod
    def poll(self, context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        icicle_props = context.scene.icicle_properties

        row = layout.row()
        col = layout.column(align=True)
        col.label(text='Radius:')
        col.prop(icicle_props, 'min_rad')
        col.prop(icicle_props, 'max_rad')

        row = layout.row()
        
        col.label(text='Depth:')
        col.prop(icicle_props, 'min_depth')
        col.prop(icicle_props, 'max_depth')

        row = layout.row()
        
        col.label(text='Loop cuts:')
        col.prop(icicle_props, 'subdivs')

        col.label(text='Cap')
        col.prop(icicle_props, 'num_verts')
        col.prop(icicle_props, 'add_cap')

        row = layout.row()
        
        layout.prop(icicle_props, 'max_its')

        # layout.prop(icicle_props, 'reselect_base')

        layout.prop(icicle_props, 'delete_previous')

        layout.prop(icicle_props, 'direction')

        label = "Preview On" if icicle_props.preview_btn_tgl else "Preview Off"
        layout.prop(icicle_props, 'preview_btn_tgl', text=label, toggle=True, icon='GPBRUSH_PEN')

        row = layout.row()
        row.operator('wm.gen_icicle', text='Generate', icon='PHYSICS')
