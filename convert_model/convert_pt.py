#!/usr/bin/env python3
import os
import argparse
import sys
from ultralytics import YOLO

def export_model(model_path, export_format, device, batch_size, workspace_gb, half, int8, imgsz, simplify):
    print(f"==================================================")
    print(f"🚀 Loading PyTorch Model: {model_path}")
    print(f"==================================================")
    
    if not os.path.exists(model_path):
        print(f"❌ Error: Model path '{model_path}' does not exist.")
        sys.exit(1)
        
    try:
        model = YOLO(model_path)
    except Exception as e:
        print(f"❌ Failed to load model using Ultralytics YOLO: {e}")
        sys.exit(1)
        
    formats_to_export = []
    if export_format == "both":
        formats_to_export = ["onnx", "engine"]
    else:
        formats_to_export = [export_format]
        
    for fmt in formats_to_export:
        print(f"\n📦 Exporting to {fmt.upper()} format (dynamic=True)...")
        try:
            # Prepare export options
            export_kwargs = {
                "format": fmt,
                "dynamic": True,
                "device": device,
                "imgsz": imgsz,
                "simplify": simplify
            }
            
            if fmt == "engine":
                if workspace_gb is not None:
                    export_kwargs["workspace"] = workspace_gb
                export_kwargs["batch"] = batch_size
                export_kwargs["half"] = half
                export_kwargs["int8"] = int8
            elif fmt == "onnx":
                # For ONNX, half=True is also supported to reduce size/speedup on some environments
                export_kwargs["half"] = half
                
            exported_path = model.export(**export_kwargs)
            print(f"✅ Successfully exported to: {exported_path}")
            
        except Exception as e:
            print(f"❌ Failed to export to {fmt}: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Convert Ultralytics YOLOv8 PyTorch (.pt) models to high-performance ONNX / TensorRT (.engine) formats.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--model", 
        type=str, 
        default="all", 
        help="Path to .pt model file, or 'all' to convert both v1 and v2 analog gauge segment models"
    )
    parser.add_argument(
        "--format", 
        type=str, 
        choices=["onnx", "engine", "both"], 
        default="both", 
        help="Target export format"
    )
    parser.add_argument(
        "--device", 
        type=str, 
        default="0", 
        help="Device to use for export (e.g., '0' for GPU, 'cpu')"
    )
    parser.add_argument(
        "--batch", 
        type=int, 
        default=8, 
        help="Max batch size for TensorRT engine"
    )
    parser.add_argument(
        "--workspace", 
        type=float, 
        default=None, 
        help="Max workspace size in GB for TensorRT engine build (None for auto-allocation)"
    )
    parser.add_argument(
        "--half",
        action="store_true",
        default=True,
        help="Enable FP16 (half-precision) quantization"
    )
    parser.add_argument(
        "--no-half",
        action="store_false",
        dest="half",
        help="Disable FP16 quantization"
    )
    parser.add_argument(
        "--int8",
        action="store_true",
        default=False,
        help="Enable INT8 quantization (requires calibration data config)"
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Input image size (imgsz)"
    )
    parser.add_argument(
        "--simplify",
        action="store_true",
        default=True,
        help="Simplify ONNX graph with onnxslim"
    )
    parser.add_argument(
        "--no-simplify",
        action="store_false",
        dest="simplify",
        help="Disable ONNX graph simplification"
    )
    
    args = parser.parse_args()
    
    # Default model files if 'all' is chosen
    v1_path = "models/analog_gauge_model/segmentation/best_segment_v1.pt"
    v2_path = "models/analog_gauge_model/segmentation/best_segment_v2.pt"
    
    models_to_convert = []
    if args.model == "all":
        base_dir = "/home/luke/gauge_inspection"
        p1 = os.path.join(base_dir, v1_path)
        p2 = os.path.join(base_dir, v2_path)
        
        if os.path.exists(p1):
            models_to_convert.append(p1)
        else:
            print(f"⚠️ Default Model v1 not found at: {p1}")
            
        if os.path.exists(p2):
            models_to_convert.append(p2)
        else:
            print(f"⚠️ Default Model v2 not found at: {p2}")
            
        if not models_to_convert:
            print("❌ No default PyTorch models found. Please specify --model path manually.")
            sys.exit(1)
    else:
        models_to_convert.append(args.model)
        
    for m in models_to_convert:
        export_model(
            m, 
            args.format, 
            args.device, 
            args.batch, 
            args.workspace, 
            args.half, 
            args.int8, 
            args.imgsz, 
            args.simplify
        )

if __name__ == "__main__":
    main()