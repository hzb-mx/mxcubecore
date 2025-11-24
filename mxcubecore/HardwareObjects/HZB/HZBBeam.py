"""
HZBBeam - Beam properties and control for BL14 beamline

Beam size, position, flux, and transmission control.
"""

import logging
from mxcubecore.HardwareObjects.BaseHardwareObjects import HardwareObject

try:
    from tango import DeviceProxy, DevFailed
    TANGO_AVAILABLE = True
except ImportError:
    TANGO_AVAILABLE = False
    logging.warning("PyTango not available - HZBBeam will run in simulation mode")


class HZBBeam(HardwareObject):
    """
    BL14 Beam implementation for beam properties and control.
    """

    def __init__(self, name):
        super().__init__(name)
        self._beam_size = (0.05, 0.05)  # mm (H, V)
        self._beam_position = (737, 839)  # pixels
        self._flux_device = None
        self._transmission_device = None
        self._transmission = 100.0  # percent

    def init(self):
        """Initialize beam control."""
        super().init()

        # Get configuration
        size_config = self.get_property("size", {})
        self._beam_size = (
            size_config.get("horizontal", 0.05),
            size_config.get("vertical", 0.05)
        )

        position_config = self.get_property("position", {})
        self._beam_position = (
            position_config.get("x", 737),
            position_config.get("y", 839)
        )

        # Connect to flux monitoring
        flux_config = self.get_property("flux", {})
        flux_device_name = flux_config.get("device", "")

        if TANGO_AVAILABLE and flux_device_name:
            try:
                self._flux_device = DeviceProxy(flux_device_name)
                self._flux_device.ping()
                logging.info(f"HZBBeam '{self.name}': Connected to flux monitor")
            except DevFailed as e:
                logging.error(f"HZBBeam '{self.name}': Failed to connect to flux monitor: {e}")
                self._flux_device = None

        # Connect to transmission control
        transmission_config = self.get_property("transmission", {})
        transmission_device_name = transmission_config.get("device", "")

        if TANGO_AVAILABLE and transmission_device_name:
            try:
                self._transmission_device = DeviceProxy(transmission_device_name)
                self._transmission_device.ping()
                logging.info(f"HZBBeam '{self.name}': Connected to transmission control")
            except DevFailed as e:
                logging.error(f"HZBBeam '{self.name}': Failed to connect to transmission: {e}")
                self._transmission_device = None

    def get_beam_size(self):
        """Get beam size in mm (horizontal, vertical)."""
        return self._beam_size

    def get_beam_position(self):
        """Get beam position on detector in pixels (x, y)."""
        return self._beam_position

    def get_flux(self):
        """Get current flux in photons/second."""
        if self._flux_device:
            try:
                return float(self._flux_device.Flux)
            except (DevFailed, AttributeError) as e:
                logging.error(f"HZBBeam '{self.name}': Error reading flux: {e}")
                return 1e12  # Simulated value
        return 1e12  # Simulated value

    def get_transmission(self):
        """Get current transmission in percent."""
        if self._transmission_device:
            try:
                return float(self._transmission_device.Transmission)
            except (DevFailed, AttributeError):
                return self._transmission
        return self._transmission

    def set_transmission(self, transmission):
        """
        Set beam transmission in percent.

        Args:
            transmission: Target transmission (0-100%)
        """
        if not (0 <= transmission <= 100):
            raise ValueError(f"HZBBeam '{self.name}': Transmission must be 0-100%")

        if self._transmission_device:
            try:
                logging.info(f"HZBBeam '{self.name}': Setting transmission to {transmission}%")
                self._transmission_device.Transmission = transmission
                self._transmission = transmission
                self.emit("transmissionChanged", (transmission,))
            except (DevFailed, AttributeError) as e:
                logging.error(f"HZBBeam '{self.name}': Error setting transmission: {e}")
        else:
            # Simulation mode
            logging.info(f"HZBBeam '{self.name}': [SIMULATION] Setting transmission to {transmission}%")
            self._transmission = transmission
            self.emit("transmissionChanged", (transmission,))
