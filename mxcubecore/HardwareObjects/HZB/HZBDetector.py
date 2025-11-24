"""
HZBDetector - Detector implementation for BL14 beamline

Pilatus3 detector control via TANGO.
"""

import logging
from mxcubecore.HardwareObjects.abstract.AbstractDetector import AbstractDetector

try:
    from tango import DeviceProxy, DevFailed
    TANGO_AVAILABLE = True
except ImportError:
    TANGO_AVAILABLE = False
    logging.warning("PyTango not available - HZBDetector will run in simulation mode")


class HZBDetector(AbstractDetector):
    """
    BL14 Detector implementation for Pilatus3 detector.
    """

    def __init__(self, name):
        super().__init__(name)
        self._tango_device = None
        self._pixel_size = (0.172, 0.172)  # mm
        self._n_pixels = (1475, 1679)
        self._exposure_time = 0.1
        self._distance = 250.0  # mm

    def init(self):
        """Initialize detector and establish TANGO connection."""
        super().init()

        # Get configuration
        tango_config = self.get_property("tango", {})
        tango_device_name = tango_config.get("device", "")

        properties = self.get_property("properties", {})
        self._pixel_size = (
            properties.get("pixel_size_x", 0.172),
            properties.get("pixel_size_y", 0.172)
        )
        self._n_pixels = (
            properties.get("n_pixels_x", 1475),
            properties.get("n_pixels_y", 1679)
        )

        defaults = self.get_property("defaults", {})
        self._exposure_time = defaults.get("exposure_time", 0.1)

        distance_config = self.get_property("distance", {})
        self._distance = distance_config.get("default", 250.0)

        # Connect to TANGO
        if TANGO_AVAILABLE and tango_device_name:
            try:
                self._tango_device = DeviceProxy(tango_device_name)
                self._tango_device.ping()
                logging.info(f"HZBDetector '{self.name}': Connected to TANGO device")
            except DevFailed as e:
                logging.error(f"HZBDetector '{self.name}': Failed to connect: {e}")
                self._tango_device = None
        else:
            logging.warning(f"HZBDetector '{self.name}': Running in simulation mode")

    def get_pixel_size(self):
        """Get detector pixel size in mm."""
        return self._pixel_size

    def get_detector_size(self):
        """Get detector dimensions in pixels."""
        return self._n_pixels

    def prepare_acquisition(self, params):
        """
        Prepare detector for data acquisition.

        Args:
            params: Dictionary with acquisition parameters
        """
        exposure = params.get("exposure_time", self._exposure_time)

        if self._tango_device:
            try:
                self._tango_device.ExposureTime = exposure
                logging.info(f"HZBDetector '{self.name}': Prepared for acquisition (exp={exposure}s)")
            except DevFailed as e:
                logging.error(f"HZBDetector '{self.name}': Error preparing acquisition: {e}")
        else:
            logging.info(f"HZBDetector '{self.name}': [SIMULATION] Prepared (exp={exposure}s)")

    def start_acquisition(self):
        """Start data acquisition."""
        if self._tango_device:
            try:
                self._tango_device.Start()
                logging.info(f"HZBDetector '{self.name}': Acquisition started")
                self.emit("acquisitionStarted", ())
            except DevFailed as e:
                logging.error(f"HZBDetector '{self.name}': Error starting acquisition: {e}")
        else:
            logging.info(f"HZBDetector '{self.name}': [SIMULATION] Acquisition started")
            self.emit("acquisitionStarted", ())

    def stop_acquisition(self):
        """Stop data acquisition."""
        if self._tango_device:
            try:
                self._tango_device.Stop()
                logging.info(f"HZBDetector '{self.name}': Acquisition stopped")
            except DevFailed as e:
                logging.error(f"HZBDetector '{self.name}': Error stopping acquisition: {e}")
        else:
            logging.info(f"HZBDetector '{self.name}': [SIMULATION] Acquisition stopped")

    def get_distance(self):
        """Get detector distance in mm."""
        if self._tango_device:
            try:
                return float(self._tango_device.Distance)
            except (DevFailed, AttributeError):
                return self._distance
        return self._distance

    def set_distance(self, distance):
        """Set detector distance in mm."""
        if self._tango_device:
            try:
                self._tango_device.Distance = distance
                logging.info(f"HZBDetector '{self.name}': Distance set to {distance} mm")
            except (DevFailed, AttributeError) as e:
                logging.error(f"HZBDetector '{self.name}': Error setting distance: {e}")
        else:
            logging.info(f"HZBDetector '{self.name}': [SIMULATION] Distance set to {distance} mm")
            self._distance = distance
