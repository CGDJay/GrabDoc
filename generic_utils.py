
import bpy, traceback, os
from bpy.types import Operator
from .render_setup_utils import get_rendered_objects


def export_bg_plane(self, context):
    # Save original selection
    savedSelection = context.selected_objects

    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # Select bg plane, export and deselect bg plane
    bpy.data.objects["GD_Background Plane"].select_set(True)
    
    bpy.ops.export_scene.fbx(
        filepath=f'{os.path.join(context.scene.grabDoc.exportPath, context.scene.grabDoc.exportName)}_plane.fbx',
        use_selection=True
    )

    bpy.data.objects["GD_Background Plane"].select_set(False)

    # Refresh original selection
    for ob in savedSelection:
        ob.select_set(True)


def proper_scene_setup(is_setup=False):
    if "GrabDoc (do not touch contents)" in bpy.data.collections:
        if "GD_Background Plane" in bpy.data.objects and "GD_Background Plane" in bpy.data.objects:
            is_setup = True
    return is_setup


def bad_setup_check(self, context, active_export, report_value=False, report_string=""):
    grabDoc = context.scene.grabDoc

    # Run this before other error checks as the following error checker contains dependencies
    get_rendered_objects(self, context)

    # Look for Trim Camera (only thing required to render)
    if not "GD_Trim Camera" in context.view_layer.objects and not report_value:
        report_value = True
        report_string = "Trim Camera not found, refresh the scene to set everything up properly."

    # Check for no objects in manual collection
    if grabDoc.onlyRenderColl and not report_value:
        if not len(bpy.data.collections["GrabDoc Objects (put objects here)"].objects):
            report_value = True
            report_string = "You have 'Use Bake Group' turned on, but no objects are inside the corresponding collection."
        
    # Checks for rendered objects that contain the Displace modifier or are 'CURVE' type objects
    #
    # TODO This just calls if the height map is turned on, not if they are
    # actually previewing it in Map Preview. This is bad, find a workaround
    if grabDoc.exportHeight and not report_value:
        for ob in context.view_layer.objects:
            if ob.name in self.render_list and grabDoc.exportHeight and grabDoc.rangeTypeHeight == 'AUTO':
                for mod in ob.modifiers:
                    if mod.type == "DISPLACE":
                        report_value = True
                        report_string = "When using Displace modifiers & baking Height you must use the 'Manual' 0-1 Range option.\n\n 'Auto' 0-1 Range cannot account for modifier geometry, this goes for all modifiers but is only required for displacement."
                        break

                if not report_value:
                    if ob.type == 'CURVE':
                        report_value = True
                        report_string = "Curves are not fully supported. When baking Height you must use the 'Manual' 0-1 Range option for accurate results." 

    if active_export:
        # Check for export path
        if not os.path.exists(grabDoc.exportPath) and not report_value:
            report_value = True
            report_string = "There is no export path set"

        # Check if all bake maps are disabled
        bake_maps = [
            grabDoc.exportNormals,
            grabDoc.exportCurvature,
            grabDoc.exportOcclusion,
            grabDoc.exportHeight,
            grabDoc.exportMatID,
            grabDoc.exportAlpha
        ]

        bake_map_vis = [
            grabDoc.uiVisibilityNormals,
            grabDoc.uiVisibilityCurvature,
            grabDoc.uiVisibilityOcclusion,
            grabDoc.uiVisibilityHeight,
            grabDoc.uiVisibilityMatID,
            grabDoc.uiVisibilityAlpha
        ]

        if not True in bake_maps or not True in bake_map_vis:
            report_value = True
            report_string = "No bake maps are turned on."

    return (report_value, report_string)


class OpInfo:
    bl_options = {'REGISTER', 'UNDO'}


class GRABDOC_OT_load_ref(OpInfo, Operator):
    """Import a reference onto the background plane"""
    bl_idname = "grab_doc.load_ref"
    bl_label = "Load Reference"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        # Load a new image into the main database
        bpy.data.images.load(self.filepath, check_existing=True)

        context.scene.grabDoc.refSelection = bpy.data.images[os.path.basename(os.path.normpath(self.filepath))]
        return{'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class GRABDOC_OT_open_folder(OpInfo, Operator):
    """Opens up the File Explorer to the designated folder location"""
    bl_idname = "grab_doc.open_folder"
    bl_label = "Open Folder"

    def execute(self, context):
        try:
            bpy.ops.wm.path_open(filepath = context.scene.grabDoc.exportPath)
        except RuntimeError:
            self.report({'ERROR'}, "No valid file path set")
        return{'FINISHED'}


class GRABDOC_OT_view_cam(OpInfo, Operator):
    """View the GrabDoc camera"""
    bl_idname = "grab_doc.view_cam"
    bl_label = "View Trim Camera"

    from_modal: bpy.props.BoolProperty(
        default=False,
        options={'HIDDEN'}
    )

    def execute(self, context):
        context.scene.camera = bpy.data.objects["GD_Trim Camera"]
        
        try:
            if self.from_modal:
                if [area.spaces.active.region_3d.view_perspective for area in context.screen.areas if area.type == 'VIEW_3D'] == ['CAMERA']:
                    bpy.ops.view3d.view_camera()
            else:
                bpy.ops.view3d.view_camera()
        except:
            traceback.print_exc()
            self.report({'ERROR'}, "Exit camera failed, please contact the developer with the error code listed in the console. ethan.simon.3d@gmail.com")

        self.from_modal = False
        return{'FINISHED'}


################################################################################################################
# REGISTRATION
################################################################################################################


classes = (
    GRABDOC_OT_open_folder,
    GRABDOC_OT_load_ref,
    GRABDOC_OT_view_cam
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####