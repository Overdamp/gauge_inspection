import numpy as np
import json
import re
import triton_python_backend_utils as pb_utils

class TritonPythonModel:
    def initialize(self, args):
        self.logger = pb_utils.Logger
        self.logger.log_info("Initializing util_ocr_postprocessor...")

    def execute(self, requests):
        responses = []
        for request in requests:
            in_data = pb_utils.get_input_tensor_by_name(request, "INPUT_DATA").as_numpy()
            
            raw_text = ""
            try:
                raw_text = in_data[0].decode("utf-8")
            except Exception:
                pass
            
            # Simple OCR post-processing logic (e.g. replacing 'O' with '0', 'l' with '1')
            processed_text = raw_text.replace("O", "0").replace("o", "0").replace("l", "1").replace("I", "1")
            
            res_dict = {
                "raw_text": raw_text,
                "processed_text": processed_text,
                "status": "success"
            }
            out_str = np.array([json.dumps(res_dict)], dtype=np.object_)
            out_tensor = pb_utils.Tensor("OUTPUT_DATA", out_str)
            responses.append(pb_utils.InferenceResponse(output_tensors=[out_tensor]))

        return responses

    def finalize(self):
        pass
