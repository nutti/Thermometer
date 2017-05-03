import bpy
from bpy.props import BoolProperty, FloatProperty, StringProperty, PointerProperty
from bpy.app.handlers import persistent
import time

bl_info = {
    "name": "Thermometer",
    "author": "Nutti",
    "version": (1, 0),
    "blender": (2, 77, 0),
    "location": "View 3D",
    "description": "Measure and Display Thermometer with Raspberry PI",
    "warning": "",
    "support": "TESTING",
    "wiki_url": "",
    "tracker_url": "",
    "category": "System"
}


def get_invoke_context(area_type, region_type):
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == area_type:
                break
        else:
            continue
        for region in area.regions:
            if region.type == region_type:
                break
        else:
            continue
        return {'window': window, 'screen': screen, 'area': area, 'region': region}


class T_Properties(bpy.types.PropertyGroup):

    running = BoolProperty(
        name="Running State",
        description="Running if True",
        default=False
    )
    temperature = FloatProperty(
        name="Temperature",
        description="Temperature measured with Raspberry PI",
        default=0.0
    )


class Thermometer(bpy.types.Operator):

    bl_idname = "system.temperature"
    bl_label = "Temperature"
    bl_description = "Measure and Display Thermometer"

    __timer = None

    def __get_temperature(self, props, prefs):
        with open(prefs.bus_path) as file:
            strs = file.readlines()
            words = strs[-1].split(" ")
            index = words[-1].find("t=")
            if index > -1:
                props.temperature = float(words[-1][2:]) / 1000.0

    def modal(self, context, event):
        props = context.scene.t_props
        prefs = context.user_preferences.addons[__name__].preferences

        if props.running is False:
            return {'FINISHED'}

        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        if context.area:
            context.area.tag_redraw()

        self.__get_temperature(props, prefs)

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        props = context.scene.t_props
        if props.running is False:
            props.running = True
            if Thermometer.__timer is None:
                Thermometer.__timer = context.window_manager.event_timer_add(
                    0.1, context.window
                )
                context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            props.running = False
            if Thermometer.__timer is not None:
                context.window_manager.event_timer_remove(Thermometer.__timer)
                Thermometer.__timer = None
            return {'FINISHED'}


class OBJECt_PT_T(bpy.types.Panel):

    bl_label = "Thermometer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        sc = context.scene
        layout = self.layout
        props = sc.t_props
        if props.running is False:
            layout.operator(
                Thermometer.bl_idname, text="Start", icon="PLAY"
            )
        else:
            layout.operator(
                Thermometer.bl_idname, text="Stop", icon="PAUSE"
            )


class T_Preferences(bpy.types.AddonPreferences):

    bl_idname = __name__

    bus_path = StringProperty(
        name="Bus",
        description="Path of the bus to get Temerature",
        default="/tmp/bus.txt"
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "bus_path")


def init_props():
    sc = bpy.types.Scene
    sc.t_props = PointerProperty(
        name="Properties",
        description="Properties for Thermometer",
        type=T_Properties
    )


def clear_props():
    sc = bpy.types.Scene
    del sc.t_props


def info_header_fn(self, context):
    layout = self.layout
    props = context.scene.t_props

    layout.label("%.1f℃" % (props.temperature), icon='BLENDER')


@persistent
def start_fn(scene):
    bpy.app.handlers.scene_update_pre.remove(start_fn)
    context = get_invoke_context('VIEW_3D', 'WINDOW')
    bpy.ops.system.temperature(context, 'INVOKE_DEFAULT')


def register():
    bpy.utils.register_module(__name__)
    init_props()
    bpy.types.INFO_HT_header.append(info_header_fn)
    bpy.app.handlers.scene_update_pre.append(start_fn)


def unregister():
    context = get_invoke_context('VIEW_3D', 'WINDOW')
    bpy.ops.system.temperature(context, 'INVOKE_DEFAULT')
    bpy.types.INFO_HT_header.remove(info_header_fn)
    clear_props()
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
