# -*- coding: utf-8 -*-
"""Validate Redshift denoiser is not used with randomized sampling.

This validator ensures that when the Redshift denoiser is enabled on the
Redshift ROP the unified sampling "Randomize Pattern" parameter is turned off.

Specifically it validates that when `RS_denoisingEnabled` is True then
`UnifiedRandomizePattern` must be False.
"""

import hou
import pyblish.api

from ayon_core.pipeline import PublishValidationError

from ayon_houdini.api import plugin
from ayon_houdini.api.action import SelectROPAction


class ValidateRedshiftDenoiserRandomizeOff(plugin.HoudiniInstancePlugin):
    """Ensure Redshift denoiser isn't combined with randomized pattern.

    Redshift documentation states that randomizing the unified sampling
    pattern across frames ("Randomize Pattern") is intended to prevent
    static noise in animations. However, when the denoiser is enabled this
    randomization can hinder consistent denoising results. As such we enforce
    that the denoiser is only enabled when the randomize pattern is disabled.
    """

    order = pyblish.api.ValidatorOrder
    families = ["redshift_rop"]
    label = "Validate Redshift Denoiser vs Randomize Pattern"
    actions = [SelectROPAction]

    def process(self, instance):
        """Run validation for the given instance.

        Parameters
        ----------
        instance : pyblish.api.Instance
            The publish instance to validate.
        """
        if not instance.data.get("instance_node"):
            # Ignore instances without an instance node (e.g. bootstrap)
            self.log.debug(
                "Skipping instance without instance node: {}".format(instance)
            )
            return

        invalid = self.get_invalid(instance)
        if invalid:
            rop = invalid[0]
            raise PublishValidationError(
                (
                    "Redshift denoiser enabled while 'Randomize Pattern' is on\n\n"
                    f"Node: {rop.path()}\n\n"
                    "Disable 'Unified Randomize Pattern' when using the denoiser, "
                    "or turn off the denoiser."
                ),
                title=self.label,
            )

    @classmethod
    def get_invalid(cls, instance):
        """Return invalid nodes when settings conflict.

        Parameters
        ----------
        instance : pyblish.api.Instance
            The publish instance to validate.

        Returns
        -------
        list[hou.Node]
            A list with the instance's ROP node when invalid, otherwise an
            empty list.
        """
        rop = hou.node(instance.data["instance_node"])  # type: ignore[index]
        if not rop:
            return []

        try:
            denoiser_enabled = bool(rop.evalParm("RS_denoisingEnabled"))
            randomize_pattern = bool(rop.evalParm("UnifiedRandomizePattern"))
        except hou.OperationFailed:
            # If parameters don't exist on the node, consider it valid
            return []

        if denoiser_enabled and randomize_pattern:
            return [rop]

        return []
