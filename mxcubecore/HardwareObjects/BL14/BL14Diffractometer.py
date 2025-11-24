"""
BL14Diffractometer - Diffractometer implementation for BL14 beamline

MD3 kappa diffractometer control.
"""

import logging
from mxcubecore.HardwareObjects.abstract.AbstractDiffractometer import AbstractDiffractometer


class BL14Diffractometer(AbstractDiffractometer):
    """
    BL14 Diffractometer implementation for MD3 kappa geometry.
    """

    def __init__(self, name):
        super().__init__(name)
        self._motors = {}
        self._centering_method = "loop"

    def init(self):
        """Initialize diffractometer."""
        super().init()

        # Get motor references from config
        motor_refs = self.get_property("motors", {})

        # Import HardwareRepository for motor access
        from mxcubecore import HardwareRepository as HWR

        # Get motor objects
        for motor_name, motor_ref in motor_refs.items():
            try:
                motor = HWR.get_hardware_object(motor_ref)
                if motor:
                    self._motors[motor_name] = motor
                    logging.info(f"BL14Diffractometer '{self.name}': Motor '{motor_name}' connected")
                else:
                    logging.warning(f"BL14Diffractometer '{self.name}': Motor '{motor_ref}' not found")
            except Exception as e:
                logging.error(f"BL14Diffractometer '{self.name}': Error loading motor '{motor_name}': {e}")

        centering_config = self.get_property("centering", {})
        self._centering_method = centering_config.get("default_method", "loop")

        logging.info(f"BL14Diffractometer '{self.name}': Initialized with {len(self._motors)} motors")

    def get_motor(self, motor_name):
        """Get motor object by name."""
        return self._motors.get(motor_name)

    def move_motors(self, motors_dict):
        """
        Move multiple motors simultaneously.

        Args:
            motors_dict: Dictionary of {motor_name: target_position}
        """
        for motor_name, position in motors_dict.items():
            motor = self._motors.get(motor_name)
            if motor:
                logging.info(f"BL14Diffractometer '{self.name}': Moving {motor_name} to {position}")
                motor.set_value(position)
            else:
                logging.warning(f"BL14Diffractometer '{self.name}': Motor '{motor_name}' not available")

    def get_positions(self):
        """Get current positions of all motors."""
        positions = {}
        for motor_name, motor in self._motors.items():
            try:
                positions[motor_name] = motor.get_value()
            except Exception as e:
                logging.error(f"BL14Diffractometer '{self.name}': Error reading {motor_name}: {e}")
                positions[motor_name] = None
        return positions

    def center_sample(self, method=None):
        """
        Center the sample using specified method.

        Args:
            method: Centering method ("loop", "xray", "optical")
        """
        method = method or self._centering_method
        logging.info(f"BL14Diffractometer '{self.name}': Centering sample using '{method}' method")

        # TODO: Implement actual centering logic
        # For now, just emit signal
        self.emit("sampleCentered", (method,))

    def abort(self):
        """Abort all motor movements."""
        logging.info(f"BL14Diffractometer '{self.name}': Aborting all motors")
        for motor_name, motor in self._motors.items():
            try:
                motor.abort()
            except Exception as e:
                logging.error(f"BL14Diffractometer '{self.name}': Error aborting {motor_name}: {e}")
