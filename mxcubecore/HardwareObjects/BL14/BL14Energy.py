"""
BL14Energy - Energy/wavelength control for BL14 beamline

Monochromator control via TANGO.
"""

import logging
from mxcubecore.HardwareObjects.abstract.AbstractEnergy import AbstractEnergy

try:
    from tango import DeviceProxy, DevFailed
    TANGO_AVAILABLE = True
except ImportError:
    TANGO_AVAILABLE = False
    logging.warning("PyTango not available - BL14Energy will run in simulation mode")


class BL14Energy(AbstractEnergy):
    """
    BL14 Energy implementation for monochromator control.
    """

    def __init__(self, name):
        super().__init__(name)
        self._tango_device = None
        self._limits = (5.0, 18.0)  # keV
        self._current_energy = 12.65  # keV

    def init(self):
        """Initialize energy control and establish TANGO connection."""
        super().init()

        # Get configuration
        tango_config = self.get_property("tango", {})
        tango_device_name = tango_config.get("device", "")

        limits_config = self.get_property("limits", {})
        self._limits = (limits_config.get("lower", 5.0), limits_config.get("upper", 18.0))

        self._current_energy = self.get_property("default", 12.65)

        # Connect to TANGO
        if TANGO_AVAILABLE and tango_device_name:
            try:
                self._tango_device = DeviceProxy(tango_device_name)
                self._tango_device.ping()
                logging.info(f"BL14Energy '{self.name}': Connected to TANGO device")
            except DevFailed as e:
                logging.error(f"BL14Energy '{self.name}': Failed to connect: {e}")
                self._tango_device = None
        else:
            logging.warning(f"BL14Energy '{self.name}': Running in simulation mode")

    def get_value(self):
        """Get current energy in keV."""
        if self._tango_device:
            try:
                return float(self._tango_device.Energy)
            except DevFailed as e:
                logging.error(f"BL14Energy '{self.name}': Error reading energy: {e}")
                return self._current_energy
        return self._current_energy

    def get_limits(self):
        """Get energy limits in keV."""
        return self._limits

    def _set_value(self, energy):
        """
        Set energy in keV.

        Args:
            energy: Target energy in keV
        """
        if not (self._limits[0] <= energy <= self._limits[1]):
            raise ValueError(f"BL14Energy '{self.name}': Energy {energy} keV out of limits {self._limits}")

        if self._tango_device:
            try:
                logging.info(f"BL14Energy '{self.name}': Setting energy to {energy} keV")
                self._tango_device.Energy = energy
                self._current_energy = energy
                self.emit("valueChanged", (energy,))
            except DevFailed as e:
                logging.error(f"BL14Energy '{self.name}': Error setting energy: {e}")
                raise RuntimeError(f"Failed to set energy: {e}")
        else:
            # Simulation mode
            logging.info(f"BL14Energy '{self.name}': [SIMULATION] Setting energy to {energy} keV")
            self._current_energy = energy
            self.emit("valueChanged", (energy,))

    def get_wavelength(self):
        """Get current wavelength in Angstroms."""
        # λ (Å) = 12.398 / E (keV)
        energy = self.get_value()
        return 12.398 / energy if energy > 0 else 0

    def set_wavelength(self, wavelength):
        """
        Set wavelength in Angstroms.

        Args:
            wavelength: Target wavelength in Angstroms
        """
        # E (keV) = 12.398 / λ (Å)
        if wavelength <= 0:
            raise ValueError(f"BL14Energy '{self.name}': Invalid wavelength {wavelength}")
        energy = 12.398 / wavelength
        self.set_value(energy)
