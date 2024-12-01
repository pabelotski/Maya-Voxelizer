# WARNING: this script requires Pillow to be installed on your device
import maya.cmds as cmds
import math
from PIL import Image, ImageDraw
from os import path


class Voxelizer(object):
    def __init__(self, width=300, height=385, voxel_size=50):
        self.window = cmds.window(title="Voxelizer v1.0", wh=(width + 4, height), menuBar=True, s=False)

        self.obj = ''
        self.container = ''
        self.fluid_shape = ''
        self.emitter = ''
        self.group_name = ''
        self.color_resolution = 0
        self.export_path = ''
        self.voxel_size = voxel_size
        # voxel_list[i] = (position, color, texture ID)
        self.voxel_list = []

        self.layout = cmds.rowColumnLayout(nc=1, w=width, h=height)


        cmds.separator(style="none", height=10, p=self.layout)
        cmds.button(l="Select Object", c=self.select_object, p=self.layout, w=width, bgc=[0.7,0.7,0.7])

        cmds.separator(style="none", height=5, p=self.layout)
        cmds.separator(style="in", height=10, p=self.layout)
        cmds.separator(style="none", height=5, p=self.layout)

        # CREATE COLUMN
        self.create_column = cmds.columnLayout(p=self.layout, cal='center', en=False)

        self.voxel_density_row = cmds.rowLayout(nc=3, p=self.create_column)
        cmds.text("Voxel Density: ", p=self.voxel_density_row, w=width / 4)
        self.voxel_density_int_field = cmds.intField(p=self.voxel_density_row, v=voxel_size, min=3, w=width/3,
                                                     cc=self.create_container, en=False)

        cmds.separator(style="none", height=5, p=self.create_column)
        self.color_check_box = cmds.checkBox(l="Use Texture", w=width, p=self.create_column, cc=self.toggle_color)

        self.texture_import_row = cmds.rowLayout(nc=4, p=self.create_column, vis=False)
        cmds.text("Texture Path: ", p=self.texture_import_row, w=width / 4.5, align='left')
        self.import_path_text_field = cmds.textField(p=self.texture_import_row, w=width / 1.7)
        cmds.button(l="Browse", c=self.select_import_texture, p=self.texture_import_row)

        cmds.separator(style="none", height=10,p=self.create_column)

        self.create_voxels_button = cmds.button(l="Create Voxels", c=self.store_values, p=self.create_column,
                                                w=width)
        # CREATE COLUMN END

        cmds.separator(style="none", height=5, p=self.layout)
        cmds.separator(style="in", height=10, p=self.layout)
        cmds.separator(style="none", height=5, p=self.layout)


        # TEXTURE COLUMN
        self.texture_column = cmds.columnLayout(p=self.layout, vis=False)
        cmds.separator(style="none", height=1, p=self.texture_column)

        self.texture_export_row = cmds.rowLayout(nc=4, p=self.texture_column)
        cmds.text("Export Path: ", p=self.texture_export_row, w=width / 4.5, align='left')
        self.export_path_text_field = cmds.textField(p=self.texture_export_row, w=width/1.7)
        cmds.button(l="Browse", c=self.select_export_folder, p=self.texture_export_row)

        cmds.separator(style="none", height=5, p=self.texture_column)
        self.texture_scale_row = cmds.rowLayout(nc=3, p=self.texture_column)
        cmds.text("Texture Scale: ", p=self.texture_scale_row, w=width / 3, align='left')
        self.texture_scale_int_field = cmds.intField(p=self.texture_scale_row, v=10, min=1, w=width / 3)

        self.color_threshold_row = cmds.rowLayout(nc=3, p=self.texture_column)
        cmds.text("Color Threshold: ", p=self.color_threshold_row, w=width / 3, align='left')
        self.color_threshold_int_field = cmds.intField(p=self.color_threshold_row, v=5, min=0, max=255, w=width / 3)
        cmds.separator(style="none", height=5, p=self.texture_column)
        self.create_texture_button = cmds.button(l="Create Texture", c=self.create_texture, p=self.texture_column,
                                                 w=width)
        cmds.separator(style="none", height=10, p=self.texture_column)
        self.move_UV_button = cmds.button(l="Move UV's", c=self.move_UV, p=self.texture_column, en=False, w=width)
        cmds.separator(style="none", height=10, p=self.texture_column)
        self.apply_texture_button = cmds.button(l="Apply Texture", c=self.apply_texture,
                                                 p=self.texture_column, en=False, w=width)
        # TEXTURE COLUMN END

        cmds.separator(style="none", height=5, p=self.layout)
        cmds.separator(style="in", height=10, p=self.layout)
        cmds.separator(style="none", height=5, p=self.layout)

        self.combine_voxels_button = cmds.button(l="Combine Into One Mesh", c=self.combine_voxels,
                                                 p=self.layout, en=False, bgc= [0.2,0.2,0.2])

        cmds.showWindow(self.window)


    def bounding_box(self, obj):
        """
        Calculates the measurements of the bounding box of the given object.
        :param obj: object to calculate box for
        :return: list [width x, height y, depth z]
        """
        bounding_box = cmds.exactWorldBoundingBox(obj)
        # returns float[x_min, y_min, z_min, x_max, y_max, z_max]
        # calculate bounding box dimensions
        box_x = bounding_box[3] - bounding_box[0]
        box_y = bounding_box[4] - bounding_box[1]
        box_z = bounding_box[5] - bounding_box[2]
        bbox = [box_x, box_y, box_z]
        return bbox


    def clear(self, clear_all:bool):
        """
        Resets all variables and deletes any geometry previously created by the script.
        :param clear_all: whether to also clear self.obj and self.voxel_list or not
        :return:
        """
        if cmds.objExists(self.container):
            cmds.delete(self.container)
        if cmds.objExists(self.emitter):
            cmds.delete(self.emitter)
        self.preview_box = ''
        self.container = ''
        self.fluid_shape = ''
        self.emitter = ''
        self.group_name = ''
        if clear_all:
            self.obj = ''
            self.voxel_list = []


    def reset(self):
        """
        Resets all UI elements back to default.
        :return:
        """
        cmds.columnLayout(self.create_column, e=True, en=True)
        cmds.columnLayout(self.texture_column, e=True, vis=False)
        cmds.rowLayout(self.texture_import_row, e=True, vis=False)
        cmds.button(self.move_UV_button, e=True, en=False)
        cmds.button(self.apply_texture_button, e=True, en=False)
        cmds.button(self.combine_voxels_button, e=True, en=False)
        cmds.checkBox(self.color_check_box, e=True, v=False)
        cmds.textField(self.import_path_text_field, e=True, tx='')
        cmds.textField(self.export_path_text_field, e=True, tx='')


    def higher_root_with_remainder(self, number:int):
        """
        Calculates what the nearest even root above the given number is, and returns both it and the difference from
        the number.
        :param number: The number to calculate the higher root for.
        :return: [higher_root, short]
        """
        root = math.sqrt(number)
        higher_root = math.ceil(root)
        short = (higher_root * higher_root) - number

        result = [higher_root, short]
        return result


    def warning_window(self, window_title: str, error_message: str):
        """
        Creates a new, small window to inform the user that there is a mistake in the input.
        :param window_title: the label of the window
        :param error_message: the message the window will display
        :return:
        """
        num_lines = error_message.count("\n")
        warning_window_height = 75
        if num_lines > 0:
            warning_window_height += 12*num_lines
        error_window = cmds.window(title=window_title, wh=(300, warning_window_height), s=False)
        cmds.showWindow(error_window)
        error_layout = cmds.rowColumnLayout(nc=1)
        cmds.separator(style="none", height=10, p=error_layout)
        cmds.text(label=error_message, p=error_layout, align="center", w=300)
        cmds.separator(style="none", height=10, p=error_layout)
        cmds.button(p=error_layout, l="OK", command="cmds.deleteUI('%s')" % error_window, align="center", w=300)


    def checkProgressEscape(self):
        """
        Checks if the progress window has been cancelled.
        :return: true if user cancelled the action, otherwise false
        """
        cancelled = cmds.progressWindow(query=True, isCancelled=True)
        if cancelled:
            cmds.progressWindow(endProgress=1)
        return cancelled


    def toggle_color(self, state: bool):
        """
        Hides or shows the texture import row and decreases or increases the window height based on the color checkbox.
        :param state: Whether the checkbox is set to True or False
        :return:
        """
        cmds.rowLayout(self.texture_import_row, e=True, vis=state)
        old_height = cmds.window(self.window, q=True, h=True)
        if state:
            new_height = old_height + 25
        else:
            new_height = old_height - 25
        cmds.window(self.window, e=True, h=new_height)


    def select_object(self, ignore):
        """
        Stores the selected object and unlocks the first section of the UI.
        :param ignore:
        :return:
        """
        target = cmds.ls(sl=True)
        amount_selected = len(target)
        print(cmds.objectType(target))
        if amount_selected == 1:
            self.clear(True)
            self.reset()
            self.obj = str(cmds.ls(sl=True, long=True))[3:-2]
            self.create_container('ignore')
            cmds.button(self.create_voxels_button, e=True, en=True)
            cmds.columnLayout(self.create_column, e=True, en=True)
            cmds.intField(self.voxel_density_int_field, e=True, en=True)
        elif amount_selected == 0:
            self.warning_window('Error', 'No object was selected!')
        elif amount_selected > 1:
            self.warning_window('Error', 'More than one object was selected!')


    def select_import_texture(self, ignore):
        """
        Opens a file dialogue for the user to select the texture of the object. Filters for image files only. The
        directory is saved inside the import path text field.
        :param ignore:
        :return:
        """
        image_filter = "Image Files (*.png *.jpg *.jpeg *.dds *.bmp *.tiff *.gif)"
        temp_path = cmds.fileDialog2(fileMode=1, dialogStyle=1, ff=image_filter)[0]
        cmds.textField(self.import_path_text_field,e=True, tx=temp_path)


    def select_export_folder(self, ignore):
        """
        Opens a file dialogue for the user to select the folder to export the new texture to.. The directory is saved
        inside the export path text field.
        :param ignore:
        :return:
        """
        temp_path = cmds.fileDialog2(fileMode=2, dialogStyle=1)[0]
        cmds.textField(self.export_path_text_field,e=True, tx=temp_path)


    def create_container(self, ignore):
        """
        Creates a 3D container and an emitter from object with the correct attributes. The container is moved to
        encapsulate the entire object.
        :param ignore:
        :return:
        """
        self.clear(False)

        # 1) create 3D container

        cmds.Create3DContainer()
        self.container = str(cmds.ls(sl=True, long=True))[3:-2]

        # create bbox to get measurements for 3D container
        bbox = self.bounding_box(self.obj)
        # round up size on all sides to be safe
        for x in range(len(bbox)):
            bbox[x] *= 1.1

        resolution = cmds.intField(self.voxel_density_int_field, q=True, v=True)
        # set attributes of 3D container
        cmds.setAttr(f'{self.container}.baseResolution', resolution)
        cmds.setAttr(f'{self.container}.dimensionsW', bbox[0])
        cmds.setAttr(f'{self.container}.dimensionsH', bbox[1])
        cmds.setAttr(f'{self.container}.dimensionsD', bbox[2])
        cmds.setAttr(f'{self.container}.densityMethod', 1)
        cmds.setAttr(f'{self.container}.colorMethod', 2)
        cmds.setAttr(f'{self.fluid_shape}.boundaryDraw', 2)

        # 2) create emitter from object

        cmds.select([self.container, self.obj])
        cmds.EmitFluidFromObject()
        cmds.select(self.container, d=True)
        self.emitter = str(cmds.ls(sl=True, long=True))[3:-2]
        cmds.setAttr(f'{self.emitter}.densityMethod', 2)
        cmds.setAttr(f'{self.container}.autoResize', 1)

        # make fluid sim use colors of mesh
        if cmds.checkBox(self.color_check_box, q=True, v=True):
            texture_path = cmds.textField(self.import_path_text_field, q=True, tx=True)
            cmds.setAttr(f'{self.emitter}.emitFluidColor', 1)
            node_name = f'{self.obj}_texture'
            # create new file render node
            cmds.createNode('file', n=node_name)
            # set texture in file
            cmds.setAttr(f'{node_name}.fileTextureName', texture_path, type='string')
            # make emitter particle color use render node
            cmds.defaultNavigation(ce=True, source=node_name, destination=f'{self.emitter}.particleColor')

        # get fluidShape name
        fluid_shapes = cmds.ls('fluidShape*')
        digits = []
        for x in range(len(fluid_shapes)):
            digit = fluid_shapes[x].replace('fluidShape', '')
            if digit.isnumeric():
                digits.append(digit)
        self.fluid_shape = f"fluidShape{max(digits)}"

        # we let the simulation run for 1 frame so the fluid container changes size according to the object
        cmds.playbackOptions(loop='once')
        cmds.playbackOptions(minTime=0, maxTime=1)
        cmds.currentTime(0)
        cmds.play(f=True, wait=True)
        cmds.playbackOptions(minTime=0, maxTime=20)

        # get center pivot of object
        old_piv = cmds.xform(self.obj, q=True, piv=True, ws=True)
        cmds.xform(self.obj, cp=True)
        center_piv = cmds.xform(self.obj, q=True, piv=True, ws=True)
        pos = cmds.xform(self.obj, q=True, piv=True, ws=True)
        # move object pivot back to original spot
        cmds.xform(self.obj, piv=(old_piv[0], old_piv[1], old_piv[2]), ws=True)
        cmds.move(pos[0], pos[1], pos[2], self.container, a=True)

        cmds.select(clear=True)


    def store_values(self, ignore):
        """
        Stores the position and color values (if applicable) of each voxel in the list. Then it deletes the container
        and emitter, and hides the object.
        :param ignore:
        :return:
        """
        i = True
        # check if user selected a texture if they wish to generate a texture
        color_check_box = cmds.checkBox(self.color_check_box, q=True, v=True)
        texture_path = cmds.textField(self.import_path_text_field, q=True, tx=True)
        if color_check_box and len(texture_path) == 0:
            result = cmds.confirmDialog(title="Warning", message="No texture selected. Continue?",
                                       button=["Yes", "Cancel"], defaultButton="Yes",
                                       cancelButton="Cancel", dismissString="Cancel")
            if result != "Yes":
                i = False
        elif color_check_box and not path.exists(texture_path):
            self.warning_window("Error", "Invalid texture path!")
            i = False

        if i:
            self.create_container('ignore')

            # 3) run simulation

            # if the simulation only runs for 1 frame, there are holes in the voxel mesh, so we let it run longer
            cmds.playbackOptions(loop='once')
            cmds.playbackOptions(minTime=0, maxTime=20)
            cmds.currentTime(0)
            cmds.play(f=True, wait=True)
            cmds.playbackOptions(minTime=0, maxTime=100)


            cmds.select(self.container)

            container_size = self.bounding_box(self.container)
            res = cmds.getAttr(f'{self.fluid_shape}.resolution')[0]
            dynamic_offset = cmds.getAttr(f'{self.fluid_shape}.dynamicOffset')[0]
            self.voxel_size = container_size[0] / res[0]

            # 4) store values

            cmds.select(self.container)

            for x in range(res[0]):
                for y in range(res[1]):
                    for z in range(res[2]):
                        density = cmds.getFluidAttr(at = 'density', xi=x, yi=y, zi=z)
                        if density[0] > 0.0:
                            color = cmds.getFluidAttr(at='color', xi=x, yi=y, zi=z)
                            # get pos of cur particle
                            c = cmds.fluidVoxelInfo(f'{self.fluid_shape}', xi=x, yi=y, zi=z, vc=True)
                            pos = (c[0] + dynamic_offset[0]), (c[1] + dynamic_offset[1]), (c[2] + dynamic_offset[2])
                            self.voxel_list.append([pos,color,0])

            cmds.hide(self.obj)
            cmds.delete([self.container, self.emitter])
            self.create_voxels()


    def create_voxels(self):
        """
        Creates the voxels in the correct positions and groups them.
        :return:
        """
        # create group
        resolution = cmds.intField(self.voxel_density_int_field, q=True, v=True)
        self.group_name = f"{self.obj}_{resolution}"
        cmds.group(empty=True, name=self.group_name)

        voxel_count = len(self.voxel_list)

        # create progress bar window
        cmds.progressWindow(title="Generating Voxels", progress=0,
                            status=f'0 of {voxel_count}', isInterruptable=True)

        for voxel in range(voxel_count):
            if self.checkProgressEscape():
                return
            # update progress bar
            amount = 100.0 / voxel_count * (voxel + 1)
            cmds.progressWindow(e=True, pr=amount, status=f'Generated {voxel} of {voxel_count}')

            pos = self.voxel_list[voxel][0]
            # create voxel
            cmds.polyCube(w=self.voxel_size, h=self.voxel_size, d=self.voxel_size)
            # move voxel to correct position
            cmds.move(pos[0], pos[1], pos[2])
            # rename voxel
            voxel_name = f"{self.group_name}_voxel_{voxel}"
            cmds.rename(voxel_name)
            cmds.parent(voxel_name, self.group_name)
        cmds.progressWindow(endProgress=1)

        cmds.button(self.combine_voxels_button, e=True, en=True)
        if cmds.checkBox(self.color_check_box, q=True, v=True):
            cmds.columnLayout(self.texture_column, e=True, vis=True)
        cmds.columnLayout(self.create_column, e=True, en=False)

        cmds.currentTime(0)
        cmds.select(clear=True)


    def create_texture(self, ignore):
        """
        Generates a texture and saves it at the user specified location. Also stores the color id of each voxel
        on the texture inside self.voxel_list[voxel][2].
        :param ignore:
        :return:
        """
        export_folder = cmds.textField(self.export_path_text_field, q=True, tx=True)

        if path.exists(export_folder):
            color_array = []
            color_threshold = cmds.intField(self.color_threshold_int_field, q=True, v=True)
            color_scale = cmds.intField(self.texture_scale_int_field, q=True, v=True)

            for voxel in range(len(self.voxel_list)):
                color_value = [0, 0, 0]
                # pillow uses 255 color system instead of a 0 to 1 float, so we have to convert the values first
                color_value[0] = round(self.voxel_list[voxel][1][0] * 255)
                color_value[1] = round(self.voxel_list[voxel][1][1] * 255)
                color_value[2] = round(self.voxel_list[voxel][1][2] * 255)

                # we loop over every existing color already in the array to compare to the current color
                is_new_color = True
                diff = [0, 0, 0]
                for color_compare in range(len(color_array)):
                    diff[0] = abs(color_array[color_compare][0] - color_value[0])
                    diff[1] = abs(color_array[color_compare][1] - color_value[1])
                    diff[2] = abs(color_array[color_compare][2] - color_value[2])
                    # if an existing color is closer than the threshold, the loop stops and the color is flagged
                    if max(diff) < color_threshold:
                        self.voxel_list[voxel][2] = color_compare
                        is_new_color = False
                        break
                # only if none of the previous colors were close enough does the color get appended to the array
                if is_new_color:
                    color_array.append(color_value)
                    self.voxel_list[voxel][2] = len(color_array)-1

            # textures need to be square, so we get the closest root above the color array count
            self.color_resolution = (self.higher_root_with_remainder(len(color_array))[0])
            # because having miniscule textures can cause issues in some software,
            # we upscale each color tile by a user specified size
            image_resolution = color_scale * self.color_resolution

            # create the image using the image resolution, and creates an object with it that can be drawn in
            img = Image.new('RGB', (image_resolution, image_resolution))
            drawing = ImageDraw.Draw(img)

            ind = 0
            break_flag = False
            for w in range(self.color_resolution):
                for h in range(self.color_resolution):
                    rect_start = (h * color_scale, w * color_scale)
                    rect_end = (h * color_scale + color_scale, w * color_scale + color_scale)
                    drawing.rectangle((rect_start, rect_end), width=0,
                                      fill=(color_array[ind][0], color_array[ind][1], color_array[ind][2]))
                    ind += 1
                    # a lot of the time, there will be more color tiles than there are colors, so we need to check if
                    # the end has been reached yet, and add black tiles for the remaining spaces
                    if ind == len(color_array):
                        color_array.append((0,0,0))

            self.export_path = f'{export_folder}\\{self.obj}_{color_threshold}.png'
            img.save(self.export_path)
            self.warning_window("Success", "Texture saved successfully.")

            cmds.button(self.move_UV_button, e=True, en=True)
        else:
            self.warning_window("Error", "Invalid export path!")


    def move_UV(self, ignore):
        """
        Goes over each voxel and moves its vertices to the location on the texture that matches its color id.
        :param ignore:
        :return:
        """

        cmds.progressWindow(title="Moving UV's", progress=0,
                            status=f'0 of {len(self.voxel_list)}', isInterruptable=True)

        for voxel in range(len(self.voxel_list)):
            if self.checkProgressEscape():
                return
            amount = 100.0 / len(self.voxel_list) * (voxel + 1)
            cmds.progressWindow(e=True, pr=amount, status=f'Moved {voxel} of {len(self.voxel_list)}')

            cmds.select(f"{self.group_name}_voxel_{voxel}")
            cmds.ConvertSelectionToUVs()
            # first, we move the uv vertices to the center of the top left pixel
            center = (1/self.color_resolution)/2
            cmds.polyEditUV(r=False,u=center,v=1-center)
            color_id = self.voxel_list[voxel][2]
            move_u = (color_id % self.color_resolution) * (1/self.color_resolution)
            move_v = math.floor(color_id/self.color_resolution) * (1/self.color_resolution)
            cmds.polyEditUV(r=True, u=move_u, v=-move_v)

        cmds.progressWindow(endProgress=1)
        cmds.select(f"{self.group_name}_voxel_0", r=True)
        cmds.select(clear=True)

        cmds.button(self.apply_texture_button, e=True, en=True)


    def apply_texture(self, ignore):
        """
        Creates a new material with a connected file node linking to the exported texture, and applies it to the voxels.
        :param ignore:
        :return:
        """
        # create new material
        density = cmds.intField(self.voxel_density_int_field, q=True, v=True)
        name = f"{self.obj}_tex_{density}"
        node_type = "lambert"
        material = cmds.shadingNode(node_type, name=name, asShader=True)
        sg = cmds.sets(name="%sSG" % name, empty=True, renderable=True, noSurfaceShader=True)
        cmds.connectAttr("%s.outColor" % material, "%s.surfaceShader" % sg)

        # create file node
        node_name = name + '_node'
        cmds.createNode('file', n=node_name)
        # select texture and store it in file
        texture_path = self.export_path
        cmds.setAttr(f'{node_name}.fileTextureName', texture_path, type='string')

        # link node to material
        cmds.defaultNavigation(ce=True, source=node_name, destination=f'{material}.color')

        # apply material to all voxels
        cmds.select(f"{self.group_name}_voxel_*", r=True)
        meshes = cmds.ls(selection=True, dag=True, type="mesh", noIntermediate=True)
        cmds.sets(meshes, forceElement=sg)

        cmds.select(clear=True)


    def combine_voxels(self, ignore):
        """
        Combines all generated voxels into a single mesh. It does NOT fuse them together.
        :param ignore:
        :return:
        """
        """
        cmds.progressWindow(title="Moving UV's", progress=0,
                            status=f'0 of {len(self.voxel_list)}', isInterruptable=True)

        cmds.select(f"{self.group_name}_voxel_0", r=True)
        cmds.rename(self.group_name+"_merged")
        for voxel in range(len(self.voxel_list)-1):
            if self.checkProgressEscape():
                return
            amount = 100.0 / len(self.voxel_list) * (voxel + 1)
            cmds.progressWindow(e=True, pr=amount, status=f'Deleted {voxel} of {len(self.voxel_list)}')

            cur_voxel = f"{self.group_name}_voxel_{voxel+1}"
            cmds.select([self.group_name+"_merged", cur_voxel], r=True)
            cmds.CombinePolygons()
            cmds.DeleteHistory()
            cmds.rename(self.group_name + "_merged")
            
        cmds.progressWindow(endProgress=1)
        """
        cmds.DeleteHistory()
        cmds.select(self.group_name, hi=True)
        cmds.CombinePolygons()
        cmds.DeleteHistory()
        cmds.rename(self.group_name)

        cmds.columnLayout(self.texture_column, e=True, en=False)


voxelizer = Voxelizer()
