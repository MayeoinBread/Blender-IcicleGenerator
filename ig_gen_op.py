import bpy
from bpy.types import Operator

import bmesh
from mathutils import Vector
from math import pi
import random

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
        wm = obj.matrix_world
        
        # Get the verts by checking the selected edge
        edge_verts = [v for v in bm.verts if v.select]
        # Make sure we only have 2 verts to use
        if len(edge_verts) != 2:
            print('Incorrect number of verts selected. Expected 2, found ' + str(len(edge_verts)))
            return
        
        # vertex coordinates
        v1 = edge_verts[0].co
        v2 = edge_verts[1].co

        # World matrix for positioning
        pos1 = wm @ v1
        pos2 = wm @ v2

        vm = pos1 - pos2
        
        # current length
        l = 0.0
        # Total length of current edge
        t_length = vm.length
        
        # Randomise the difference between radii, add it to the min and don't go over the max value
        rad_dif = my_props.max_rad - my_props.min_rad
        rand_rad = min(my_props.min_rad + (rad_dif * random.random()), my_props.max_rad)
        
        # Depth, as with radius above
        depth_dif = my_props.max_depth - my_props.min_depth
        rand_depth = min(my_props.min_depth + (depth_dif * random.random()), my_props.max_depth)

        # Get user iterations
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
        while l < t_length and c < iterations:
            # Check depth is bigger then radius
            # Icicles generally longer than wider
            if it_depth > it_rad:
                # Check that we won't overshoot the length of the line
                # By using a cone of this radius
                if l + (2 * it_rad) <= t_length:
                    l += it_rad
                    t_co = pos2 + (l / t_length) * vm
                    l += it_rad
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
                print ('Maximumiterations reached on edge')

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
            oEdge = [e for e in bm.edges if e.select]
        else:
            oEdge = [e for e in bm.edges]
    
        for e in oEdge:
            # Check for vertical edge before working on it
            if e.verts[0].co.x == e.verts[1].co.x and e.verts[0].co.y == e.verts[1].co.y:
                self.verticalEdges = True
                continue
            # Deselect everything and select the current edge
            bpy.ops.mesh.select_all(action='DESELECT')
            bm.edges.ensure_lookup_table()
            e.select = True
            self.add_icicles(context, my_props)
        
        # Reselect the initial selection if desired
        if my_props.reselect_base:
            bpy.ops.mesh.select_all(action='DESELECT')
            bm.edges.ensure_lookup_table()
            for e in oEdge:
                e.select = True

    def execute(self, context):
        scene = bpy.context.scene
        myprop = scene.my_props

        # Check variables aren't bigger than they should be
        if myprop.min_rad > myprop.max_rad:
            myprop.max_rad = myprop.min_rad
        
        if myprop.min_depth > myprop.max_depth:
            myprop.max_depth = myprop.min_depth
        
        self.verticalEdges = False

        # Run the function
        obj = context.active_object
        
        if obj and obj.type == 'MESH':
            if obj.mode != 'EDIT':
                self.report({'INFO'}, "Icicles cannot be added outside Edit mode")
            else:
                check = self.runIt(context, myprop)
                
                if check is False:
                    self.report({'INFO'}, "Operation could not be completed")
                    
                if self.verticalEdges:
                    self.report({'INFO'}, "Some vertical edges were skipped during icicle creation")
        else:
            self.report({'INFO'}, "Cannot generate on non-Mesh object")
        
        return {'FINISHED'}
