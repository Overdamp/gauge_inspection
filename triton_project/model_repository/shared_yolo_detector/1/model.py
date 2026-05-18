import numpy as np
import triton_python_backend_utils as pb_utils

class TritonPythonModel:
    def initialize(self, args):
        self.logger = pb_utils.Logger
        self.logger.log_info("Initializing shared_yolo_detector...")

    def execute(self, requests):
        responses = []
        for request in requests:
            # Stub outputs: 1 detection box, class 0 (gauge/screen), score 0.95
            boxes = np.array([[100.0, 150.0, 500.0, 600.0]], dtype=np.float32)
            classes = np.array([0], dtype=np.int32)
            scores = np.array([0.95], dtype=np.float32)

            out_boxes = pb_utils.Tensor("DETECTION_BOXES", boxes)
            out_classes = pb_utils.Tensor("DETECTION_CLASSES", classes)
            out_scores = pb_utils.Tensor("DETECTION_SCORES", scores)

            responses.append(pb_utils.InferenceResponse(output_tensors=[out_boxes, out_classes, out_scores]))

        return responses

    def finalize(self):
        pass
