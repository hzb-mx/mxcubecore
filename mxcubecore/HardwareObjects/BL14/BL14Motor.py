"""
BL14Motor - Motor implementation for BL14 beamline

Supports both rotation and translation motors via TANGO control system.
"""

import logging
from mxcubecore.HardwareObjects.abstract.AbstractMotor import AbstractMotor

try:
    from tango import DeviceProxy, DevFailed
    TANGO_AVAILABLE = True
except ImportError:
    TANGO_AVAILABLE = False
    logging.warning("PyTango not available - BL14Motor will run in simulation mode")


class BL14Motor(AbstractMotor):
    """
    BL14 Motor implementation using TANGO control system.

    Supports both rotation (omega, phi, kappa) and translation (sample_x, sample_y) motors.
    """

    def __init__(self, name):
        super().__init__(name)
        self._tango_device = None
        self._motor_type = None
        self._limits = [-360, 360]
        self._velocity = 1.0
        self._unit = "degree"
        self._precision = 0.001
        self._simulation_position = 0.0

    def init(self):
        """Initialize the motor and establish TANGO connection."""
        super().init()

        # Get configuration from YAML
        tango_config = self.get_property("tango", {})
        tango_device_name = tango_config.get("device", "")

        properties = self.get_property("properties", {})
        self._unit = properties.get("unit", "degree")
        self._precision = properties.get("precision", 0.001)
        self._velocity = properties.get("velocity", 1.0)

        limits_config = self.get_property("limits", {})
        self._limits = [limits_config.get("lower", -360), limits_config.get("upper", 360)]

        self._motor_type = self.get_property("type", "rotation")

        # Connect to TANGO device
        if TANGO_AVAILABLE and tango_device_name:
            try:
                self._tango_device = DeviceProxy(tango_device_name)
                self._tango_device.ping()
                logging.info(f"BL14Motor '{self.name}': Connected to TANGO device {tango_device_name}")
                self._update_state()
            except DevFailed as e:
                logging.error(f"BL14Motor '{self.name}': Failed to connect to TANGO device: {e}")
                self._tango_device = None
        else:
            logging.warning(f"BL14Motor '{self.name}': Running in simulation mode")

    def _update_state(self):
        """Update motor state from TANGO device."""
        if self._tango_device:
            try:
                # Read state and position
                state = self._tango_device.State()
                self._simulation_position = float(self._tango_device.Position)

                # Emit state change signal
                self.emit("stateChanged", (str(state),))
            except DevFailed as e:
                logging.error(f"BL14Motor '{self.name}': Error reading state: {e}")

    def get_value(self):
        """Get current motor position."""
        if self._tango_device:
            try:
                return float(self._tango_device.Position)
            except DevFailed as e:
                logging.error(f"BL14Motor '{self.name}': Error reading position: {e}")
                return self._simulation_position
        else:
            return self._simulation_position

    def get_limits(self):
        """Get motor limits."""
        return tuple(self._limits)

    def get_velocity(self):
        """Get motor velocity."""
        return self._velocity

    def _set_value(self, value):
        """
        Move motor to target position.

        Args:
            value: Target position
        """
        # Validate limits
        if not (self._limits[0] <= value <= self._limits[1]):
            raise ValueError(
                f"BL14Motor '{self.name}': Position {value} out of limits {self._limits}"
            )

        if self._tango_device:
            try:
                logging.info(f"BL14Motor '{self.name}': Moving to {value} {self._unit}")
                self._tango_device.Position = value
                self.emit("valueChanged", (value,))
            except DevFailed as e:
                logging.error(f"BL14Motor '{self.name}': Error moving motor: {e}")
                raise RuntimeError(f"Failed to move motor: {e}")
        else:
            # Simulation mode
            logging.info(f"BL14Motor '{self.name}': [SIMULATION] Moving to {value} {self._unit}")
            self._simulation_position = value
            self.emit("valueChanged", (value,))

    def abort(self):
        """Abort motor movement."""
        if self._tango_device:
            try:
                self._tango_device.Stop()
                logging.info(f"BL14Motor '{self.name}': Aborted")
            except DevFailed as e:
                logging.error(f"BL14Motor '{self.name}': Error aborting: {e}")
        else:
            logging.info(f"BL14Motor '{self.name}': [SIMULATION] Aborted")

    def stop(self):
        """Stop motor movement (alias for abort)."""
        self.abort()

    def home(self):
        """Home the motor."""
        if self._tango_device:
            try:
                self._tango_device.Home()
                logging.info(f"BL14Motor '{self.name}': Homing")
            except DevFailed as e:
                logging.error(f"BL14Motor '{self.name}': Error homing: {e}")
        else:
            logging.info(f"BL14Motor '{self.name}': [SIMULATION] Homing")
            self._simulation_position = 0.0

    def get_state(self):
        """Get motor state."""
        if self._tango_device:
            try:
                state = self._tango_device.State()
                return str(state)
            except DevFailed:
                return "UNKNOWN"
        else:
            return "SIMULATION"
