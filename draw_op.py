import bpy
import bmesh

import bgl
import blf

import gpu
from gpu_extras.batch import batch_for_shader

from bpy.types import Operator
import math
import mathutils

from . ig_gen_op import check_same_2d

# class OT_draw_operator(Operator):
class OT_Draw_Preview(Operator):
    bl_idname = "wm.icicle_preview"
    bl_label = "Icicle preview"
    bl_description = "Operator for drawing icicle previews"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        return (ob and ob.mode == 'EDIT')
        
    def __init__(self):
        self.draw_handle_3d = None
        self.draw_event  = None

        self.ice_props = bpy.context.scene.icegen_props
        self.vert_array = []

        self.create_batch()

    def invoke(self, context, event):
        args = (self, context)

        if self.draw_handle_3d is None:
            self.register_handlers(args, context)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def register_handlers(self, args, context):
        self.draw_handle_3d = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_callback_3d, args, "WINDOW", "POST_VIEW"
        )

        self.draw_event = context.window_manager.event_timer_add(0.1, window=context.window)

    def unregister_handlers(self, context):
        context.window_manager.event_timer_remove(self.draw_event)

        bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_3d, "WINDOW")

        self.draw_handle_3d = None
        self.draw_event = None

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()

        # Check toggle button to finish showing preview
        if not self.ice_props.preview_btn_tgl:
            self.unregister_handlers(context)
            return {'FINISHED'}

        # Check ESC key press to cancel preview
        if event.type in {'ESC'}:
            self.unregister_handlers(context)
            self.ice_props.preview_btn_tgl = False
            return {'CANCELLED'}
        
        return {'PASS_THROUGH'}

    def create_batch(self):
        obj = bpy.context.object
        bm = bmesh.from_edit_mesh(obj.data)
        wm = obj.matrix_world

        # Get edges based on selection criteria
        if self.ice_props.on_selected_edges:
            s_edges = [e for e in bm.edges if e.select and not check_same_2d(e, self.ice_props.min_rad)]
        else:
            s_edges = [e for e in bm.edges if not check_same_2d(e, self.ice_props.min_rad)]

        # Find midpoint of each edge to position preview of icicles
        for e in s_edges:
            v_dir = (e.verts[0].co - e.verts[1].co).normalized() @ wm
            mid_point = (e.verts[0].co + e.verts[1].co) * 0.5
            self.vert_array.append((mid_point, v_dir))

    def draw_callback_3d(self, op, context):
        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        shader.bind()

        # Don't use XRay mode
        bgl.glEnable(bgl.GL_DEPTH_TEST)
        bgl.glLineWidth(1.5)

        # Get direction
        m_dir = -1 if self.ice_props.direction == 'Up' else 1

        for mid_point, v_dir in self.vert_array:
            v_r_dir = mathutils.Vector((v_dir.y, v_dir.x, v_dir.z))
            shader.uniform_float('color', (0, 1, 1, 1))
            # min size icicle
            min_icicle = [
                mid_point + (self.ice_props.min_rad * v_dir),
                mid_point - (m_dir * self.ice_props.min_depth * mathutils.Vector((0, 0, 1))),
                mid_point - (self.ice_props.min_rad * v_dir)
            ]
            min_icicle_r = [
                mid_point + (self.ice_props.min_rad * v_r_dir),
                mid_point - (m_dir * self.ice_props.min_depth * mathutils.Vector((0, 0, 1))),
                mid_point - (self.ice_props.min_rad * v_r_dir)
            ]
            sq_1 = [min_icicle[0], min_icicle_r[0], min_icicle[2], min_icicle_r[2], min_icicle[0]]
            batch = batch_for_shader(shader, 'LINE_STRIP', {"pos":min_icicle})
            batch.draw(shader)
            # min_icicle_t = [x.transposed() for x in min_icicle]
            batch = batch_for_shader(shader, 'LINE_STRIP', {"pos":min_icicle_r})
            batch.draw(shader)
            batch = batch_for_shader(shader, 'LINE_STRIP', {"pos":sq_1})
            batch.draw(shader)

            shader.uniform_float('color', (0, 0, 1, 1))
            # max size icicle
            max_icicle = [
                mid_point + (self.ice_props.max_rad * v_dir),
                mid_point - (m_dir * self.ice_props.max_depth * mathutils.Vector((0, 0, 1))),
                mid_point - (self.ice_props.max_rad * v_dir)
            ]
            max_icicle_r = [
                mid_point + (self.ice_props.max_rad * v_r_dir),
                mid_point - (m_dir * self.ice_props.max_depth * mathutils.Vector((0, 0, 1))),
                mid_point - (self.ice_props.max_rad * v_r_dir)
            ]
            sq_2 = [max_icicle[0], max_icicle_r[0], max_icicle[2], max_icicle_r[2], max_icicle[0]]
            batch = batch_for_shader(shader, 'LINE_STRIP', {"pos":max_icicle})
            batch.draw(shader)
            batch = batch_for_shader(shader, 'LINE_STRIP', {"pos":max_icicle_r})
            batch.draw(shader)
            batch = batch_for_shader(shader, 'LINE_STRIP', {"pos":sq_2})
            batch.draw(shader)

