# -*- coding: utf-8 -*-
"""HZB Energy control using SPEC command wrapper.

BL14.1 production uses SPEC command 'prodc_set_mono' on bl141:spec server
to control the monochromator motor.
"""

import logging
from mxcubecore.HardwareObjects.abstract.AbstractEnergy import AbstractEnergy

__copyright__ = "Copyright © 2025 by the MXCuBE collaboration"
__license__ = "LGPLv3+"


class HZBEnergy(AbstractEnergy):
    """HZB Energy control via SPEC command."""

    def __init__(self, name):
        super().__init__(name)
        self.spec_connection = None
        self.spec_command = None
        self.spec_version = None
        self.command_name = None

    def init(self):
        """Initialize SPEC connection and command."""
        super().init()

        # Get SPEC configuration from YAML
        spec_config = self.get_property("spec", {})
        self.spec_version = spec_config.get("version", "bl141:spec")
        self.command_name = spec_config.get("command", "prodc_set_mono")

        # Lazy import to avoid hard dependency on SpecClient
        try:
            from SpecClient_gevent import SpecConnection, SpecCommand

            self.spec_connection = SpecConnection.SpecConnection(self.spec_version)
            self.spec_command = SpecCommand.SpecCommand(
                self.command_name, self.spec_connection
            )

            logging.getLogger("HWR").info(
                f"HZBEnergy: Connected to SPEC {self.spec_version}, "
                f"command '{self.command_name}'"
            )
        except ImportError:
            logging.getLogger("HWR").warning(
                "HZBEnergy: SpecClient_gevent not available, SPEC control disabled"
            )
            self.spec_connection = None
            self.spec_command = None

    def get_value(self):
        """Read current energy value.

        Note: Production XML does not specify a SPEC channel for reading energy.
        This may rely on the motor object (/energymot) or a separate channel.
        For now, return cached value or None.

        Returns:
            (float): Current energy [keV] or None if unavailable.
        """
        # TODO: Determine how to read current energy from SPEC
        # Options:
        # 1. Query SPEC motor position via motor_name
        # 2. Subscribe to a SPEC channel (if available)
        # 3. Maintain cached value from last set operation
        logging.getLogger("HWR").debug(
            "HZBEnergy.get_value(): Reading energy not yet implemented"
        )
        return self._nominal_value

    def _set_value(self, value):
        """Set energy by calling SPEC command.

        Args:
            value (float): Target energy [keV]
        """
        if self.spec_command is None:
            raise RuntimeError(
                "HZBEnergy: SPEC command not available. "
                "Check SPEC connection and SpecClient installation."
            )

        logging.getLogger("HWR").info(
            f"HZBEnergy: Setting energy to {value} keV via SPEC command '{self.command_name}'"
        )

        try:
            # Execute SPEC command with energy value as argument
            self.spec_command(value)
            self._nominal_value = value
        except Exception as e:
            logging.getLogger("HWR").error(
                f"HZBEnergy: Failed to set energy: {e}"
            )
            raise

    def abort(self):
        """Abort energy change operation."""
        if self.spec_connection:
            try:
                # Send abort command to SPEC (if supported)
                self.spec_connection.abort()
                logging.getLogger("HWR").info("HZBEnergy: Aborted energy change")
            except Exception as e:
                logging.getLogger("HWR").warning(
                    f"HZBEnergy: Abort failed: {e}"
                )

    def get_limits(self):
        """Get energy limits.

        Returns:
            (tuple): (min_energy, max_energy) in keV
        """
        limits_config = self.get_property("limits", {})
        return (
            limits_config.get("lower", 5.0),
            limits_config.get("upper", 18.0)
        )
