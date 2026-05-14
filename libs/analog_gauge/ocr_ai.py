import os
os.environ["LRU_CACHE_CAPACITY"] = "1"
os.environ["TORCH_CPP_LOG_LEVEL"] = "ERROR"

import cv2
import json
import numpy as np
import torch
from torchvision.transforms.v2 import Resize, Compose, ToImage, ToDtype
from doctr.models import recognition

class DoctrOCR:
    def __init__(self, model_dir: str, device: str = "cpu"):
        self.device = device
        self.model_dir = model_dir
        
        config_path = os.path.join(model_dir, "config.json")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config not found at {config_path}")
            
        with open(config_path, "r") as f:
            self.cfg = json.load(f)
            
        self.vocab = self.cfg.get("vocab")
        self.input_size = tuple(self.cfg.get("INPUT_SIZE", [32, 128]))
        self.model_arch = self.cfg.get("MODEL_ARCH", "parseq")
        
        self.use_onnx = False
        onnx_path = "/home/luke/gauge_inspection/model_conversion/ocr_model.onnx"
        
        if os.path.exists(onnx_path) and "cuda" in self.device.lower():
            try:
                import onnxruntime as ort
                providers = [
                    ('TensorrtExecutionProvider', {
                        'device_id': 0,
                        'trt_max_workspace_size': 2147483648,
                        'trt_fp16_enable': True,
                    }),
                    'CUDAExecutionProvider'
                ]
                self.ort_session = ort.InferenceSession(onnx_path, providers=providers)
                self.use_onnx = True
                print(f"🚀 OCR High-Performance Mode: Using ONNX with TensorRT Provider")
            except Exception as e:
                print(f"⚠️ Could not load ONNX session: {e}. Falling back to PyTorch.")

        # โหลดโมเดล PyTorch สำหรับกรณีปกติ หรือใช้เพื่อถอดรหัส (Decode) ในโหมด ONNX
        self.model = recognition.__dict__[self.model_arch](
            pretrained=False, 
            vocab=self.vocab, 
            input_shape=(3, self.input_size[0], self.input_size[1])
        )
        
        if not self.use_onnx:
            ckpt_path = os.path.join(model_dir, "best_model.pt")
            if not os.path.exists(ckpt_path):
                raise FileNotFoundError(f"Checkpoint not found at {ckpt_path}")
                
            state_dict = torch.load(ckpt_path, map_location=self.device)
            if "model_state_dict" in state_dict:
                state_dict = state_dict["model_state_dict"]
                
            clean_state_dict = {k.replace("module.", ""): v for k, v in state_dict.items()}
            self.model.load_state_dict(clean_state_dict)
            self.model.to(self.device)
            self.model.eval()
        
        self.transforms = Compose([
            ToImage(),
            ToDtype(torch.float32, scale=True),
            Resize(self.input_size, antialias=True),
        ])

    def predict(self, img_bgr: np.ndarray):
        res = self.predict_batch([img_bgr])
        return res[0]

    def predict_batch(self, images_list: list):
        if not images_list: return []
        
        tensors = []
        for img_bgr in images_list:
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            tensors.append(self.transforms(img_rgb))
        
        img_batch = torch.stack(tensors).to(self.device)
        
        results = []
        if self.use_onnx:
            # Inference ด้วย ONNX Runtime (TensorRT)
            # หมายเหตุ: ถ้า ONNX ของเราไม่ได้ทำ Dynamic Batch ไว้ อาจจะต้องวนลูปข้างในนี้
            # แต่ปกติ ONNX ที่เรา Export มา (opset 17) จะรองรับ Dynamic Batch อยู่แล้ว
            ort_inputs = {self.ort_session.get_inputs()[0].name: img_batch.cpu().numpy()}
            ort_outs = self.ort_session.run(None, ort_inputs)
            logits = torch.from_numpy(ort_outs[0])
            
            with torch.no_grad():
                # Decode ทีละตัวใน Batch
                for i in range(len(logits)):
                    out = self.model.decode(logits[i:i+1])
                    results.append(out[0])
        else:
            # Inference ด้วย PyTorch ปกติ (Batch Mode)
            with torch.no_grad():
                output = self.model(img_batch, target=None, return_preds=True)
                
            if "preds" in output:
                results = output['preds']
            else:
                # กรณีโมเดลคืนค่ามาแบบอื่น
                results = output
                
        return [(text, float(conf)) for text, conf in results]