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
import bmesh

import bgl
import blf

import gpu
from gpu_extras.batch import batch_for_shader

from bpy.types import Operator

class OT_draw_operator(Operator):
    bl_idname = "object.draw_op"
    bl_label = "Draw operator"
    bl_description = "Operator for drawing" 
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if context.object == None:
            return True

        return context.object.mode == 'EDIT'
    	
    def __init__(self):
        self.draw_handle_3d = None
        self.draw_event  = None

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

        if event.type == 'ESC' and event.value == 'PRESS':
            self.unregister_handlers(context)
            return {'FINISHED'}
        
        return {'PASS_THROUGH'}

    def finish(self):
        self.unregister_handlers(bpy.context)
        return {'FINISHED'}

    def points_same_2d(self, edge):
        v1 = edge.verts[0]
        v2 = edge.verts[1]

        equal = v1.co.x == v2.co.x and v1.co.y == v2.co.y

        return equal


    def create_batch(self):
        obj = bpy.context.object
        bm = bmesh.from_edit_mesh(obj.data)
        wm = obj.matrix_world

        scene = bpy.context.scene
        ice_prop = scene.icegen_props

        self.min_array = []
        self.max_array = []

        self.shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')

        if ice_prop.on_selected_edges:
            s_edges = [e for e in bm.edges if e.select and not self.points_same_2d(e)]
        else:
            s_edges = [e for e in bm.edges if not self.points_same_2d(e)]

        for e in s_edges:
            v1 = wm @ e.verts[0].co
            v2 = wm @ e.verts[1].co

            v_dir = (v2 - v1).normalized() @ wm

            mid_point = (v1 + v2) * 0.5

            min_icicle = [
                mid_point + (ice_prop.min_rad / 2) * v_dir,
                mid_point - ice_prop.min_depth * Vector((0, 0, 1)),
                mid_point - (ice_prop.min_rad / 2) * v_dir
            ]

            max_icicle = [
                mid_point + (ice_prop.max_rad / 2) * v_dir,
                #(mid_point.x, mid_point.y, mid_point.z - ice_prop.max_depth),
                mid_point - ice_prop.max_depth * Vector((0, 0, 1)),
                mid_point - (ice_prop.max_rad / 2) * v_dir
            ]

            self.min_array.append(batch_for_shader(self.shader, 'LINE_STRIP', {'pos':min_icicle}))
            self.max_array.append(batch_for_shader(self.shader, 'LINE_STRIP', {'pos':max_icicle}))

    def draw_callback_3d(self, op, context):
        bgl.glEnable(bgl.GL_LINE_SMOOTH)
        self.shader.bind()

        self.shader.uniform_float('color', (1, 0, 0, 1))
        bgl.glLineWidth(1)
        for b_min in self.min_array:
            b_min.draw(self.shader)

        self.shader.uniform_float('color', (0, 1, 0, 1))
        bgl.glLineWidth(2)
        for b_max in self.max_array:
            b_max.draw(self.shader)
