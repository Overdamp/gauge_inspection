import os
import sys
import numpy as np
import triton_python_backend_utils as pb_utils

sys.path.append("/home/luke/gauge_inspection")
from cores.config_loader import load_config
from libs.analog_gauge import DoctrOCR

class TritonPythonModel:
    def initialize(self, args):
        self.logger = pb_utils.Logger
        self.logger.log_info("Initializing doctr_ocr...")
        
        os.chdir("/home/luke/gauge_inspection")
        
        config = load_config("configs/config.yaml")
        ocr_model_dir = config.get("analog_gauge", {}).get("ocr_model_dir", "")
        ocr_device = config.get("analog_gauge", {}).get("device", "cpu")
        
        self.ocr_model = DoctrOCR(model_dir=ocr_model_dir, device=ocr_device)
        self.logger.log_info("doctr_ocr loaded successfully.")

    def execute(self, requests):
        responses = []
        for request in requests:
            in_image = pb_utils.get_input_tensor_by_name(request, "IMAGE").as_numpy()
            
            try:
                text, conf = self.ocr_model.predict(in_image)
            except Exception as e:
                self.logger.log_error(f"OCR predict failed: {e}")
                text, conf = "", 0.0

            text_tensor = pb_utils.Tensor("TEXT_RESULT", np.array([text], dtype=object))
            conf_tensor = pb_utils.Tensor("CONFIDENCE", np.array([conf], dtype=np.float32))
            
            responses.append(pb_utils.InferenceResponse(output_tensors=[text_tensor, conf_tensor]))

        return responses

    def finalize(self):
        pass
