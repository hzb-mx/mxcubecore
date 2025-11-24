"""
BL14Collect - Data collection orchestration for BL14 beamline

Coordinates detector, diffractometer, beam, and energy for data collection.
"""

import logging
from mxcubecore.HardwareObjects.abstract.AbstractCollect import AbstractCollect


class BL14Collect(AbstractCollect):
    """
    BL14 Data Collection implementation.

    Orchestrates hardware components for data collection workflows.
    """

    def __init__(self, name):
        super().__init__(name)
        self._diffractometer = None
        self._detector = None
        self._beam = None
        self._energy = None

    def init(self):
        """Initialize collect object and get hardware references."""
        super().init()

        # Get hardware object references
        from mxcubecore import HardwareRepository as HWR

        requires = self.get_property("requires", [])

        for hw_name in requires:
            try:
                hw_obj = HWR.get_hardware_object(hw_name)
                if hw_obj:
                    setattr(self, f"_{hw_name}", hw_obj)
                    logging.info(f"BL14Collect '{self.name}': Connected to '{hw_name}'")
                else:
                    logging.warning(f"BL14Collect '{self.name}': Hardware '{hw_name}' not found")
            except Exception as e:
                logging.error(f"BL14Collect '{self.name}': Error loading '{hw_name}': {e}")

        logging.info(f"BL14Collect '{self.name}': Initialized")

    def collect(self, params):
        """
        Execute data collection with given parameters.

        Args:
            params: Dictionary with collection parameters
                - exposure_time: Exposure time in seconds
                - n_images: Number of images to collect
                - oscillation_range: Oscillation range per image (degrees)
                - start_angle: Starting angle (degrees)
                - transmission: Beam transmission (0-100%)
                - energy: Energy in keV (optional)
        """
        logging.info(f"BL14Collect '{self.name}': Starting data collection")
        logging.info(f"  Parameters: {params}")

        try:
            # Set energy if specified
            if "energy" in params and self._energy:
                self._energy.set_value(params["energy"])

            # Set transmission if specified
            if "transmission" in params and self._beam:
                self._beam.set_transmission(params["transmission"])

            # Prepare detector
            if self._detector:
                self._detector.prepare_acquisition(params)

            # Move to start angle
            if "start_angle" in params and self._diffractometer:
                omega_motor = self._diffractometer.get_motor("omega")
                if omega_motor:
                    omega_motor.set_value(params["start_angle"])

            # Start acquisition
            if self._detector:
                self._detector.start_acquisition()

            self.emit("collectionStarted", (params,))

            # TODO: Implement actual collection loop
            # For now, just emit finished signal
            logging.info(f"BL14Collect '{self.name}': Collection completed")
            self.emit("collectionFinished", (params,))

        except Exception as e:
            logging.error(f"BL14Collect '{self.name}': Collection failed: {e}")
            self.emit("collectionFailed", (str(e),))
            raise

    def prepare_collection(self, params):
        """
        Prepare for data collection (pre-checks, validation).

        Args:
            params: Collection parameters dictionary
        """
        logging.info(f"BL14Collect '{self.name}': Preparing collection")

        # Validate parameters
        required_params = ["exposure_time", "n_images", "oscillation_range"]
        for param in required_params:
            if param not in params:
                raise ValueError(f"Missing required parameter: {param}")

        # Check hardware availability
        if not self._detector:
            raise RuntimeError("Detector not available")
        if not self._diffractometer:
            raise RuntimeError("Diffractometer not available")

        logging.info(f"BL14Collect '{self.name}': Preparation complete")

    def abort(self):
        """Abort ongoing data collection."""
        logging.info(f"BL14Collect '{self.name}': Aborting collection")

        if self._detector:
            self._detector.stop_acquisition()
        if self._diffractometer:
            self._diffractometer.abort()

        self.emit("collectionAborted", ())
