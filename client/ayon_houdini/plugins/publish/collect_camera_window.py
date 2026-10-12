# -*- coding: utf-8 -*-
"""Collect camera screen window (lens shift) data for camera publishes.

BCN customization: Alembic stores the camera window offset as film offset,
but Nuke's Alembic camera reader ignores it. The values collected here are
stored in the version data under `cameraWindow` so the Nuke camera loader
can apply them to the camera's `win_translate` and `win_scale` knobs.

Data layout (`versionData["cameraWindow"]`):
    frameStart (int): Frame of the first value in any per-frame list.
    resx, resy (int), pixelAspect (float): Image format of the camera.
    winx, winy, winsizex, winsizey: A float when constant over the frame
        range, otherwise a list with one float per frame from `frameStart`.
"""
import hou
import pyblish.api

from ayon_houdini.api import plugin


class CollectCameraWindow(plugin.HoudiniInstancePlugin):
    """Collect camera window offset and size for camera products."""

    # After CollectRopFrameRange
    order = pyblish.api.CollectorOrder + 0.1
    families = ["camera"]
    label = "Collect Camera Window"

    window_parms = ("winx", "winy", "winsizex", "winsizey")

    def process(self, instance):
        rop_node = hou.node(instance.data.get("instance_node") or "")
        if rop_node is None or rop_node.parm("objects") is None:
            return

        camera = hou.node("{}/{}".format(
            rop_node.evalParm("root"), rop_node.evalParm("objects")))
        if camera is None or camera.type().name() != "cam":
            self.log.debug("No camera node found on %s", rop_node.path())
            return

        frame_start = instance.data.get("frameStartHandle")
        frame_end = instance.data.get("frameEndHandle")
        if frame_start is None or frame_end is None:
            frame_start = frame_end = hou.frame()
        frame_start, frame_end = int(frame_start), int(frame_end)
        frames = range(frame_start, frame_end + 1)

        data = {
            "frameStart": frame_start,
            "resx": camera.parm("resx").evalAtFrame(frame_start),
            "resy": camera.parm("resy").evalAtFrame(frame_start),
            "pixelAspect": camera.parm("aspect").evalAtFrame(frame_start),
        }
        for parm_name in self.window_parms:
            parm = camera.parm(parm_name)
            values = [parm.evalAtFrame(frame) for frame in frames]
            if all(value == values[0] for value in values):
                data[parm_name] = values[0]
            else:
                data[parm_name] = values

        self.log.debug("Collected camera window: %s", {
            key: value for key, value in data.items()
            if not isinstance(value, list)
        })
        instance.data.setdefault("versionData", {})["cameraWindow"] = data
