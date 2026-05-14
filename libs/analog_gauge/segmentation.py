import torch
from ultralytics import YOLO
import numpy as np
import os
from typing import List, Dict, Any

class GaugeSegmentor:
    def __init__(self, config: dict):
        self.config = config
        self.model_path = self.config.get('model_path', '')
        self.conf = self.config.get('conf', 0.5)
        self.iou = self.config.get('iou', 0.5)
        self.verbose = self.config.get('verbose', False)
        
       
        requested_device = self.config.get('device', 0)
        if isinstance(requested_device, (int, list)) and not torch.cuda.is_available():
            print("Warning: GPU requested but CUDA is not available. Falling back to CPU for Segmentation.")
            self.device = 'cpu'
        else:
            self.device = requested_device
            
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            # ตรวจสอบว่ามีไฟล์ TensorRT (.engine) หรือไม่
            engine_path = self.model_path.replace(".pt", ".engine")
            
            # ถ้าเป็น Path สัมพัทธ์ ให้ลองหาจากตำแหน่งโปรเจกต์หลัก
            if not os.path.isabs(engine_path):
                # หาตำแหน่งโปรเจกต์ (ขึ้นไป 2 ระดับจากไฟล์นี้)
                current_file_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.abspath(os.path.join(current_file_dir, "../../"))
                alt_path = os.path.join(project_root, engine_path)
                if os.path.exists(alt_path):
                    engine_path = alt_path

            if os.path.exists(engine_path):
                self.model_path = engine_path
                print(f"🚀 Found TensorRT engine: {self.model_path}. Using High-Performance mode.")

            self.model = YOLO(self.model_path,task='segment')
            print(f"Successfully loaded segmentation model from {self.model_path} on {self.device}")
            
        except Exception as e:
            print(f"Error during segmentation model loading: {e}")

    def get_segmentation(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        bbox, class และ mask (polygon points)
        """
        if self.model is None: return []
        
        results = self.model.predict(
            source=image, 
            conf=self.conf, 
            iou=self.iou, 
            device=self.device, 
            verbose=self.verbose,
            retina_masks=True,
            save= False  
        )
        
        segmentations = []
        for result in results:
            if result.masks is None:
                continue

          
            try:
              
                xyxys = result.boxes.xyxy.cpu().numpy().astype(int)   # (N,4)
                clss  = result.boxes.cls.cpu().numpy().astype(int)    # (N,)
                confs = result.boxes.conf.cpu().numpy()               # (N,)

                
                masks_xy_list = list(result.masks.xy)                 # len = M
            except Exception as e:
                continue

            n = min(len(xyxys), len(masks_xy_list))  # Protect N != M
            for i in range(n):
                label = self.model.names[clss[i]]
                mask_points = masks_xy_list[i].astype(int)
                #mask_points = masks_xy_list[i].astype(np.float32) เดี๋ยวลองใช้ float32 ดูว่าดีกว่าไหม

                segmentations.append({
                    "bbox":  xyxys[i].tolist(),
                    "mask":  mask_points.tolist(),
                    "class": label,
                    "conf":  float(confs[i]),
                })

        return segmentations

    def crop_object(self, image: np.ndarray, bbox: list) -> np.ndarray:
        x1, y1, x2, y2 = bbox
        h, w = image.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        return image[y1:y2, x1:x2]