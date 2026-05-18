import os
import sys
import json
import numpy as np
import triton_python_backend_utils as pb_utils

sys.path.append("/home/luke/gauge_inspection")
from cores.config_loader import load_config
from libs.analog_gauge.segmentation import GaugeSegmentor

class TritonPythonModel:
    def initialize(self, args):
        self.logger = pb_utils.Logger
        self.logger.log_info("Initializing analog_seg...")
        
        # Change working directory so relative paths in config work
        os.chdir("/home/luke/gauge_inspection")
        
        config = load_config("configs/config.yaml")
        seg_config = config.get("analog_gauge", {}).get("segmentation", {})
        
        self.segmentor = GaugeSegmentor(seg_config)
        self.logger.log_info("analog_seg loaded successfully.")

    def execute(self, requests):
        responses = []
        for request in requests:
            in_image = pb_utils.get_input_tensor_by_name(request, "IMAGE").as_numpy()
            
            # Run segmentation
            try:
                segmentations = self.segmentor.get_segmentation(in_image)
            except Exception as e:
                self.logger.log_error(f"Segmentation failed: {e}")
                segmentations = []

            # We need to convert mask_points to lists for JSON serialization
            json_friendly_segs = []
            if segmentations:
                for seg in segmentations:
                    # seg['mask'] is a list of points or numpy array
                    mask_pts = seg.get('mask', [])
                    if isinstance(mask_pts, np.ndarray):
                        mask_pts = mask_pts.tolist()
                        
                    bbox = seg.get('bbox', [])
                    if isinstance(bbox, np.ndarray):
                        bbox = bbox.tolist()

                    json_friendly_segs.append({
                        "class": seg.get('class', ''),
                        "conf": float(seg.get('conf', 0.0)),
                        "mask": mask_pts,
                        "bbox": bbox
                    })

            json_str = json.dumps(json_friendly_segs)
            out_tensor = pb_utils.Tensor("SEG_JSON", np.array([json_str], dtype=object))
            
            responses.append(pb_utils.InferenceResponse(output_tensors=[out_tensor]))

        return responses

    def finalize(self):
        pass
