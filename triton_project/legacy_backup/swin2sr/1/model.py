import os
import sys
import numpy as np
import triton_python_backend_utils as pb_utils

sys.path.append("/home/luke/gauge_inspection")
from cores.config_loader import load_config
from libs.analog_gauge import GaugeScaleSuperResolution

class TritonPythonModel:
    def initialize(self, args):
        self.logger = pb_utils.Logger
        self.logger.log_info("Initializing swin2sr...")
        
        os.chdir("/home/luke/gauge_inspection")
        
        config = load_config("configs/config.yaml")
        sr_config = config.get("analog_gauge", {}).get("superresolution", {})
        
        self.superresolution = GaugeScaleSuperResolution(sr_config)
        self.logger.log_info("swin2sr loaded successfully.")

    def execute(self, requests):
        responses = []
        for request in requests:
            in_image = pb_utils.get_input_tensor_by_name(request, "IMAGE").as_numpy()
            
            try:
                out_image = self.superresolution.get_superresolution(in_image)
            except Exception as e:
                self.logger.log_error(f"SuperResolution failed: {e}")
                import cv2
                # Fallback to simple resize
                out_image = cv2.resize(in_image, (0, 0), fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

            out_tensor = pb_utils.Tensor("IMAGE_SR", out_image)
            responses.append(pb_utils.InferenceResponse(output_tensors=[out_tensor]))

        return responses

    def finalize(self):
        pass
