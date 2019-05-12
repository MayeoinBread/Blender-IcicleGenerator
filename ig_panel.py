import bpy_types
from bpy.types import Panel

class OBJECT_PT_CustomPanel(Panel):
    bl_idname = 'OBJECT_PT_custom_panel'
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
        scene = context.scene
        myprop = scene.my_props

        row = layout.row()
        layout.prop(myprop, 'on_selected_edges')

        row = layout.row()
        
        col = layout.column(align=True)
        col.label(text='Radius:')
        col.prop(myprop, 'min_rad')
        col.prop(myprop, 'max_rad')

        row = layout.row()
        
        col.label(text='Depth:')
        col.prop(myprop, 'min_depth')
        col.prop(myprop, 'max_depth')

        row = layout.row()
        
        col.label(text='Loop cuts:')
        col.prop(myprop, 'subdivs')

        col.label(text='Cap')
        col.prop(myprop, 'num_verts')
        col.prop(myprop, 'add_cap')

        row = layout.row()
        
        layout.prop(myprop, 'max_its')

        layout.prop(myprop, 'reselect_base')

        row = layout.row()
        # row.operator('object.draw_op', text='Draw', icon='GPBRUSH_PEN')
        row.operator('wm.gen_icicle', text='Generate', icon='PHYSICS')