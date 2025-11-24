"""
BL14SampleChanger - Sample changer implementation for BL14 beamline

CAT (CATS-like) sample changer control via TANGO.
"""

import logging
from mxcubecore.HardwareObjects.abstract.AbstractSampleChanger import AbstractSampleChanger

try:
    from tango import DeviceProxy, DevFailed
    TANGO_AVAILABLE = True
except ImportError:
    TANGO_AVAILABLE = False
    logging.warning("PyTango not available - BL14SampleChanger will run in simulation mode")


class BL14SampleChanger(AbstractSampleChanger):
    """
    BL14 Sample Changer implementation for CAT system.
    """

    def __init__(self, name):
        super().__init__(name)
        self._tango_device = None
        self._loaded_sample = None
        self._n_baskets = 9
        self._n_samples_per_basket = 10

    def init(self):
        """Initialize sample changer and establish TANGO connection."""
        super().init()

        # Get configuration
        tango_config = self.get_property("tango", {})
        tango_device_name = tango_config.get("device", "")

        properties = self.get_property("properties", {})
        self._n_baskets = properties.get("n_baskets", 9)
        self._n_samples_per_basket = properties.get("n_samples_per_basket", 10)

        # Connect to TANGO
        if TANGO_AVAILABLE and tango_device_name:
            try:
                self._tango_device = DeviceProxy(tango_device_name)
                self._tango_device.ping()
                logging.info(f"BL14SampleChanger '{self.name}': Connected to TANGO device")
            except DevFailed as e:
                logging.error(f"BL14SampleChanger '{self.name}': Failed to connect: {e}")
                self._tango_device = None
        else:
            logging.warning(f"BL14SampleChanger '{self.name}': Running in simulation mode")

    def get_sample_list(self):
        """Get list of available samples."""
        samples = []
        for basket in range(1, self._n_baskets + 1):
            for position in range(1, self._n_samples_per_basket + 1):
                samples.append({
                    "basket": basket,
                    "position": position,
                    "location": f"{basket}:{position:02d}",
                    "barcode": None,
                    "present": True  # In simulation, assume all present
                })
        return samples

    def load_sample(self, sample_location):
        """
        Load sample from specified location.

        Args:
            sample_location: Sample location string (e.g., "1:05" for basket 1, position 5)
        """
        logging.info(f"BL14SampleChanger '{self.name}': Loading sample {sample_location}")

        if self._tango_device:
            try:
                self._tango_device.LoadSample(sample_location)
                self._loaded_sample = sample_location
                self.emit("sampleLoaded", (sample_location,))
                logging.info(f"BL14SampleChanger '{self.name}': Sample {sample_location} loaded")
            except DevFailed as e:
                logging.error(f"BL14SampleChanger '{self.name}': Error loading sample: {e}")
                raise RuntimeError(f"Failed to load sample: {e}")
        else:
            # Simulation mode
            logging.info(f"BL14SampleChanger '{self.name}': [SIMULATION] Sample {sample_location} loaded")
            self._loaded_sample = sample_location
            self.emit("sampleLoaded", (sample_location,))

    def unload_sample(self):
        """Unload current sample."""
        if self._loaded_sample:
            logging.info(f"BL14SampleChanger '{self.name}': Unloading sample {self._loaded_sample}")

            if self._tango_device:
                try:
                    self._tango_device.UnloadSample()
                    sample = self._loaded_sample
                    self._loaded_sample = None
                    self.emit("sampleUnloaded", (sample,))
                    logging.info(f"BL14SampleChanger '{self.name}': Sample unloaded")
                except DevFailed as e:
                    logging.error(f"BL14SampleChanger '{self.name}': Error unloading sample: {e}")
                    raise RuntimeError(f"Failed to unload sample: {e}")
            else:
                # Simulation mode
                logging.info(f"BL14SampleChanger '{self.name}': [SIMULATION] Sample unloaded")
                sample = self._loaded_sample
                self._loaded_sample = None
                self.emit("sampleUnloaded", (sample,))
        else:
            logging.warning(f"BL14SampleChanger '{self.name}': No sample to unload")

    def get_loaded_sample(self):
        """Get currently loaded sample location."""
        return self._loaded_sample

    def abort(self):
        """Abort sample changer operation."""
        if self._tango_device:
            try:
                self._tango_device.Abort()
                logging.info(f"BL14SampleChanger '{self.name}': Aborted")
            except DevFailed as e:
                logging.error(f"BL14SampleChanger '{self.name}': Error aborting: {e}")
        else:
            logging.info(f"BL14SampleChanger '{self.name}': [SIMULATION] Aborted")
