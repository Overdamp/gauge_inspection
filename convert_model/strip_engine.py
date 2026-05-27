#!/usr/bin/env python3
import struct
import os

def strip_ultralytics_header(input_path, output_path):
    print(f"🔄 Stripping Ultralytics header from: {input_path}")
    if not os.path.exists(input_path):
        print(f"❌ Error: Input file '{input_path}' not found.")
        return False
        
    try:
        with open(input_path, "rb") as f:
            # Read the 4-byte header length
            len_bytes = f.read(4)
            if len(len_bytes) < 4:
                print("❌ Error: File is too small.")
                return False
                
            header_len = struct.unpack("<I", len_bytes)[0]
            print(f"📋 Detected header length: {header_len} bytes")
            
            # Skip the JSON header
            f.seek(4 + header_len)
            
            # Read the rest of the file (the raw TensorRT engine)
            raw_engine = f.read()
            
            # Verify magic bytes
            if len(raw_engine) < 4:
                print("❌ Error: Raw engine data is too small.")
                return False
                
            magic = raw_engine[:4]
            if magic == b'ftrt':
                print("✅ Valid TensorRT magic bytes 'ftrt' detected!")
            else:
                print(f"⚠️ Warning: Expected 'ftrt' magic bytes, but found {magic}. Writing anyway...")
                
            # Write out the clean plan file
            with open(output_path, "wb") as out_f:
                out_f.write(raw_engine)
            print(f"💾 Clean TensorRT engine saved to: {output_path} ({len(raw_engine) / (1024*1024):.2f} MB)")
            return True
            
    except Exception as e:
        print(f"❌ Failed to strip header: {e}")
        return False

def main():
    base_dir = "/home/luke/gauge_inspection"
    
    # Version 1
    v1_in = os.path.join(base_dir, "models/analog_gauge_model/segmentation/best_segment_v1.engine")
    v1_out = os.path.join(base_dir, "triton_project/model_repository/shared_analog_seg/1/model.plan")
    
    # Version 2
    v2_in = os.path.join(base_dir, "models/analog_gauge_model/segmentation/best_segment_v2.engine")
    v2_out = os.path.join(base_dir, "triton_project/model_repository/shared_analog_seg/2/model.plan")
    
    # Perform stripping
    strip_ultralytics_header(v1_in, v1_out)
    strip_ultralytics_header(v2_in, v2_out)

if __name__ == "__main__":
    main()
