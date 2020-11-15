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
from bpy.types import Operator

import bmesh
from mathutils import Vector
from math import pi
import random


def vertical_difference_check(edge):
    # TODO update buffer at some point
    return abs(edge.verts[0].co.z - edge.verts[1].co.z) > 0.01


# Get z co-ordinate, used for sorting
def get_vertex_z(vert):
    return vert.co.z

  
def check_same_2d(m_edge, min_rad):
    # Return True if verts are too close together
    e1_2d = Vector(((m_edge.verts[0].co.x, m_edge.verts[0].co.y)))
    e2_2d = Vector(((m_edge.verts[1].co.x, m_edge.verts[1].co.y)))
    d_2d = (e1_2d - e2_2d).length
    
    # Check that edge is long enough to fit the smallest cone
    if d_2d <= 2 * min_rad:
        return True
    return False


class WM_OT_GenIcicle(Operator):
    bl_idname = 'wm.gen_icicle'
    bl_label = 'Generate Icicles'
    bl_options = {'REGISTER', 'UNDO'}

    def pos_neg(self):
        return -1 if random.random() < 0.5 else 1

    ##
    # Add cone function
    ##
    def add_cone(self, loc_vector, base_rad, cone_depth):
        rot = (0.0 if self.ice_prop.direction == 'Up' else pi, 0.0, 0.0)
        loc = loc_vector + (cone_depth / 2) * Vector((0, 0, 1)) if self.ice_prop.direction == 'Up' else loc_vector - (cone_depth / 2) * Vector((0, 0, 1))
        bpy.ops.mesh.primitive_cone_add(
            vertices = self.ice_prop.num_verts,
            radius1 = base_rad,
            radius2 = 0.0,
            depth = cone_depth,
            end_fill_type = self.ice_prop.add_cap,
            align = 'WORLD',
            # Adjust the Z-height to account for the depth of the cone
            # As pivot point is in the centre of the mesh
            location = loc,
            rotation = rot
            )

    ##
    # Add icicle function
    ##
    def add_icicles(self, context):
        obj = context.object
        bm = bmesh.from_edit_mesh(obj.data)
        world_matrix = obj.matrix_world
        self.ice_prop = context.scene.icicle_properties
        
        # Get the verts by checking the selected edge
        edge_verts = [v for v in bm.verts if v.select]
        # Make sure we only have 2 verts to use
        if len(edge_verts) != 2:
            print('Incorrect number of verts selected. Expected 2, found {}'.format(len(edge_verts)))
            return
        
        # vertex coordinates
        v1 = edge_verts[0].co
        v2 = edge_verts[1].co

        # World matrix for positioning
        pos1 = world_matrix @ v1
        pos2 = world_matrix @ v2

        # Total length of current edge
        total_length = (pos1 - pos2).length
        
        # current length
        c_length = 0.0
        # Randomise the difference between radii, add it to the min and don't go over the max value
        rad_dif = self.ice_prop.max_rad - self.ice_prop.min_rad
        rand_rad = min(self.ice_prop.min_rad + (rad_dif * random.random()), self.ice_prop.max_rad)
        
        # Depth, as with radius above
        depth_dif = self.ice_prop.max_depth - self.ice_prop.min_depth
        rand_depth = min(self.ice_prop.min_depth + (depth_dif * random.random()), self.ice_prop.max_depth)

        # Get user iterations Max
        iterations = self.ice_prop.max_its
        # Counter for iterations
        c = 0

        # Set up vars for the loop
        it_rad = rand_rad
        it_depth = rand_depth
        wh_ratio = it_depth / it_rad
        if wh_ratio < 1:
            max_cuts = min(1, self.ice_prop.subdivs)
        else:
            max_cuts = self.ice_prop.subdivs
        num_cuts = random.randint(0, max_cuts)

        # List to hold calculated points to add cones
        edge_points = []

        c = 0
        while c_length < total_length and c < iterations:
            # Check that 2 * min_rad can fit inside the remaining space
            if (total_length - c_length) < (2 * self.ice_prop.min_rad):
                break
            # # Check depth is bigger then radius
            # # Icicles generally longer than wider
            # if it_depth > it_rad:
            # Check that we won't overshoot the length of the line
            # By using a cone of this radius
            if c_length + (2 * it_rad) <= total_length:
                c_length += it_rad
                t_co = pos2 + (c_length / total_length) * (pos1 - pos2)
                c_length += it_rad
                # Set up a random variable to offset the subdivisions on the icicle if added
                t_rand = min(it_rad * 0.45, it_rad) * self.pos_neg()
                edge_points.append((t_co, it_rad, it_depth, num_cuts, t_rand))

            # Re-calculate values for next iteration
            it_rad = min(self.ice_prop.min_rad + (rad_dif * random.random()), self.ice_prop.max_rad)
            it_depth = min(self.ice_prop.min_depth + (depth_dif * random.random()), self.ice_prop.max_depth)
            wh_ratio = it_depth / it_rad
            if self.ice_prop.subdivs > 0:
                if wh_ratio < 1:
                    max_cuts = min(1, self.ice_prop.subdivs)
                else:
                    max_cuts = self.ice_prop.subdivs
                num_cuts = random.randint(1, max_cuts)
            else:
                num_cuts = 0

            # Increment by 1, check for max reached
            c += 1
            if c >= iterations:
                self.max_its_reached = True
                # print ('Maximum iterations reached on edge')

        # Loop through list of calculated points and add a cone
        # Then subdivide and shift to alter the straightness
        for cpoint, rad, depth, cuts, offset in edge_points:
            # Add the cone
            self.add_cone(cpoint, rad, depth)
            # Check that we're going to subdivide, and that we're going to shift them a noticable amount
            if cuts > 0:  # and abs(offset) > 0.02:
                bm.edges.ensure_lookup_table()
                # Get the vertical edges only so we can subdivide
                vertical_edges = [e for e in bm.edges if e.select and vertical_difference_check(e)]
                ret = bmesh.ops.subdivide_edges(bm, edges=vertical_edges, cuts=cuts)
                # Get the newly-generated verts so we can shift them
                new_verts = [v for v in ret['geom_split'] if type(v) is bmesh.types.BMVert]
                # Sort so we work from top down
                new_verts.sort(key=get_vertex_z, reverse=True)
                for t in range(cuts):
                    v_z = new_verts[0].co.z
                    bpy.ops.mesh.select_all(action='DESELECT')
                    # add buffer of +/- 0.04 in case vert height isn't exactly exact
                    for v in (v for v in new_verts if -0.04 < v.co.z - v_z < 0.04):
                        v.select = True
                    # Move the edge loop
                    # TODO vertical offset based off (depth / num_cuts)
                    bpy.ops.transform.translate(value=(offset, offset, 0))
                    # Generate new offset value, and (try) make it less effective as we go down the icicle
                    offset = offset * random.random() * abs((1-t)/cuts)
                obj.data.update()

    ##
    # Run function
    ##        
    def runIt(self, context):
        obj = context.object
        bm = bmesh.from_edit_mesh(obj.data)
        bm.edges.ensure_lookup_table()
        ice_props = context.scene.icicle_properties

        # Make sure we're in Edge select mode
        bpy.ops.mesh.select_mode(type='EDGE')
        
        # List of initial edges
        original_edges = [e for e in bm.edges if e.select]
        if ice_props.delete_previous:
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.delete(type='EDGE')
    
        for idx, m_edge in enumerate(original_edges):
            # Check for vertical edge before working on it
            e1_2d = Vector((m_edge.verts[0].co.x, m_edge.verts[0].co.y))
            e2_2d = Vector((m_edge.verts[1].co.x, m_edge.verts[1].co.y))
            d_2d = (e1_2d - e2_2d).length
            
            # Check that edge is long enough to fit the smallest cone
            if d_2d <= 2 * ice_props.min_rad:
                # print("{} - Edge too small".format(idx))
                continue

            # Deselect everything and select the current edge
            bpy.ops.mesh.select_all(action='DESELECT')
            bm.edges.ensure_lookup_table()
            m_edge.select = True
            self.add_icicles(context)
        
        # Reselect the initial selection if desired
        if ice_props.reselect_base:
            bpy.ops.mesh.select_all(action='DESELECT')
            bm.edges.ensure_lookup_table()
            for e in original_edges:
                e.select = True

    def execute(self, context):
        scene = bpy.context.scene
        ice_prop = scene.icicle_properties

        # Check variables aren't bigger than they should be
        if ice_prop.min_rad > ice_prop.max_rad:
            ice_prop.max_rad = ice_prop.min_rad
        
        if ice_prop.min_depth > ice_prop.max_depth:
            ice_prop.max_depth = ice_prop.min_depth
        
        self.verticalEdges = False
        self.max_its_reached = False

        # Run the function
        obj = context.active_object
        
        if obj and obj.type == 'MESH':
            if obj.mode != 'EDIT':
                self.report({'INFO'}, "Icicles cannot be added outside Edit mode")
            else:
                try:
                    self.runIt(context)
                except IndexError:
                    self.report({'ERROR'}, "Issue generating icicles")

                if self.verticalEdges:
                    self.report({'INFO'}, "Some edges were skipped during icicle creation - line too steep")

                if self.max_its_reached:
                    self.report({'INFO'}, "Maximum iterations reached on some edges, may be missing some icicles")
        else:
            self.report({'INFO'}, "Cannot generate on non-Mesh object")
        
        return {'FINISHED'}
