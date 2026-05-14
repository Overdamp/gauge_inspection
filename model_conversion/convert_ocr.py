import os
import torch
import torch.onnx
from doctr.models import recognition
import json

def convert_ocr_to_onnx(model_dir, output_path):
    config_path = os.path.join(model_dir, "config.json")
    with open(config_path, "r") as f:
        cfg = json.load(f)
        
    vocab = cfg.get("vocab")
    input_size = tuple(cfg.get("INPUT_SIZE", [32, 128]))
    model_arch = cfg.get("MODEL_ARCH", "parseq")
    
    # 1. Load Model
    print(f"📦 Loading DocTR OCR model: {model_arch}")
    model = recognition.__dict__[model_arch](
        pretrained=False, 
        vocab=vocab, 
        input_shape=(3, input_size[0], input_size[1])
    )
    
    ckpt_path = os.path.join(model_dir, "best_model.pt")
    state_dict = torch.load(ckpt_path, map_location="cpu")
    if "model_state_dict" in state_dict:
        state_dict = state_dict["model_state_dict"]
    clean_state_dict = {k.replace("module.", ""): v for k, v in state_dict.items()}
    model.load_state_dict(clean_state_dict)
    
    # สำคัญ: ตั้งค่าเป็น exportable เพื่อให้รองรับ ONNX (สำหรับ PARSeq)
    if hasattr(model, 'exportable'):
        model.exportable = True
        
    model.eval()

    # 2. Export to ONNX
    dummy_input = torch.randn(1, 3, input_size[0], input_size[1])
    print(f"🚀 Exporting to ONNX: {output_path}")
    # Export to ONNX with Opset 18 (More stable for PARSeq/Unsqueeze)
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=18,
        do_constant_folding=True,
        input_names=['IMAGE'],
        output_names=['TEXT_RESULT'],
        dynamic_axes={
            'IMAGE': {0: 'batch_size'},
            'TEXT_RESULT': {0: 'batch_size'}
        }
    )
    print("✅ ONNX export successful!")
    print(f"💡 Next step: run 'trtexec --onnx={output_path} --saveEngine={output_path.replace('.onnx', '.engine')} --fp16'")

if __name__ == "__main__":
    model_dir = "/home/luke/gauge_inspection/models/analog_gauge_model/ocr"
    output_onnx = "/home/luke/gauge_inspection/model_conversion/ocr_model.onnx"
    convert_ocr_to_onnx(model_dir, output_onnx)
