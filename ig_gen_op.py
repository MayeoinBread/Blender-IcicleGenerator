import bpy
from bpy.types import Operator

import bmesh
from mathutils import Vector
from math import pi
import random


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
    def add_cone(self, num_verts, loc_vector, base_rad, cone_depth, cone_cap, direction):
        rot = (0.0 if direction == 'Up' else pi, 0.0, 0.0)
        loc = loc_vector + (cone_depth / 2) * Vector((0, 0, 1)) if direction == 'Up' else loc_vector - (cone_depth / 2) * Vector((0, 0, 1))
        bpy.ops.mesh.primitive_cone_add(
            vertices = num_verts,
            radius1 = base_rad,
            radius2 = 0.0,
            depth = cone_depth,
            end_fill_type = cone_cap,
            align = 'WORLD',
            # Adjust the Z-height to account for the depth of the cone
            # As pivot point is in the centre of the mesh
            location = loc,
            rotation = rot
            )

    # Get z co-ordinate, used for sorting
    def get_z(self, vert):
        return vert.co.z

    ##
    # Add icicle function
    ##
    def add_icicles(self, context, my_props):
        obj = context.object
        bm = bmesh.from_edit_mesh(obj.data)
        world_matrix = obj.matrix_world
        
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
        rad_dif = my_props.max_rad - my_props.min_rad
        rand_rad = min(my_props.min_rad + (rad_dif * random.random()), my_props.max_rad)
        
        # Depth, as with radius above
        depth_dif = my_props.max_depth - my_props.min_depth
        rand_depth = min(my_props.min_depth + (depth_dif * random.random()), my_props.max_depth)

        # Get user iterations Max
        iterations = my_props.max_its
        # Counter for iterations
        c = 0

        # Set up vars for the loop
        it_rad = rand_rad
        it_depth = rand_depth
        num_cuts = random.randint(0, my_props.subdivs)

        # List to hold calculated points to add cones
        edge_points = []

        c = 0
        while c_length < total_length and c < iterations:
            # Check that 2 * min_rad can fit inside the remaining space
            if (total_length - c_length) < (2 * my_props.min_rad):
                break
            # Check depth is bigger then radius
            # Icicles generally longer than wider
            if it_depth > it_rad:
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
            it_rad = min(my_props.min_rad + (rad_dif * random.random()), my_props.max_rad)
            it_depth = min(my_props.min_depth + (depth_dif * random.random()), my_props.max_depth)
            num_cuts = random.randint(0, my_props.subdivs)

            # Increment by 1, check for max reached
            c += 1
            if c >= iterations:
                print ('Maximum iterations reached on edge')

        # Loop through list of calculated points and add a cone
        # Then subdivide and shift to alter the straightness
        for cpoint, rad, depth, cuts, offset in edge_points:
            # Add the cone
            self.add_cone(my_props.num_verts, cpoint, rad, depth, my_props.add_cap, my_props.direction)
            # Check that we're going to subdivide, and that we're going to shift them a noticable amount
            if cuts > 0 and abs(offset) > 0.02:
                bm.edges.ensure_lookup_table()
                # Get the vertical edges only so we can subdivide
                vertical_edges = [e for e in bm.edges if e.select and e.verts[0].co.z != e.verts[1].co.z]
                ret = bmesh.ops.subdivide_edges(bm, edges=vertical_edges, cuts=cuts)
                # Get the newly-generated verts so we can shift them
                new_verts = [v for v in ret['geom_split'] if type(v) is bmesh.types.BMVert]
                # Sort so we work from top down
                new_verts.sort(key=self.get_z, reverse=True)
                for t in range(cuts):
                    v_z = new_verts[0].co.z
                    bpy.ops.mesh.select_all(action='DESELECT')
                    # add buffer of +/- 0.04 in case vert height isn't exactly exact
                    for v in (v for v in new_verts if -0.04 < v.co.z - v_z < 0.04):
                        v.select = True
                    # Move the edge loop
                    bpy.ops.transform.translate(value=(offset, offset, offset))
                    # Generate new offset value, and (try) make it less effective as we go down the icicle
                    offset = offset * random.random() * abs((1-t)/cuts)
                obj.data.update()

    ##
    # Run function
    ##        
    def runIt(self, context, my_props):
        obj = context.object
        bm = bmesh.from_edit_mesh(obj.data)
        bm.edges.ensure_lookup_table()
        
        # List of initial edges
        if my_props.on_selected_edges:
            original_edges = [e for e in bm.edges if e.select]
        else:
            original_edges = [e for e in bm.edges]
    
        for idx, m_edge in enumerate(original_edges):
            # Check for vertical edge before working on it
            if check_same_2d(m_edge, my_props.min_rad):
                # print("{} - Edge too small".format(idx))
                if abs(m_edge.verts[0].co.z - m_edge.verts[1].co.z) > my_props.min_depth:
                    self.vertical_edges = True
                else:
                    self.short_edge = True
                continue

            # Deselect everything and select the current edge
            bpy.ops.mesh.select_all(action='DESELECT')
            bm.edges.ensure_lookup_table()
            m_edge.select = True
            self.add_icicles(context, my_props)
        
        # Reselect the initial selection if desired
        if my_props.reselect_base:
            bpy.ops.mesh.select_all(action='DESELECT')
            bm.edges.ensure_lookup_table()
            for e in original_edges:
                e.select = True

    def execute(self, context):
        scene = bpy.context.scene
        myprop = scene.icegen_props

        # Check variables aren't bigger than they should be
        if myprop.min_rad > myprop.max_rad:
            myprop.max_rad = myprop.min_rad
        
        if myprop.min_depth > myprop.max_depth:
            myprop.max_depth = myprop.min_depth
        
        self.vertical_edges = False
        self.short_edge = False

        # Run the function
        obj = context.active_object
        
        if obj and obj.type == 'MESH':
            if obj.mode != 'EDIT':
                self.report({'INFO'}, "Icicles cannot be added outside Edit mode")
            else:
                self.runIt(context, myprop)
                
                if self.vertical_edges:
                    self.report({'INFO'}, "Some edges were skipped during icicle creation - line too steep")
                if self.short_edge:
                    self.report({'INFO'}, "Some edges were skipped during icicle creation - edge too short")
        else:
            self.report({'INFO'}, "Cannot generate on non-Mesh object")
        
        return {'FINISHED'}
