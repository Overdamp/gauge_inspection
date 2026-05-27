import struct

with open("models/analog_gauge_model/segmentation/best_segment_v2.engine", "rb") as f:
    # Read the 4-byte length
    len_bytes = f.read(4)
    header_len = struct.unpack("<I", len_bytes)[0]
    print("Header length:", header_len)
    
    # Read the JSON metadata
    meta_json = f.read(header_len).decode("utf-8", errors="ignore")
    print("Meta JSON:", meta_json[:200] + "...")
    
    # Read the next 100 bytes (which should be the start of the raw TRT engine)
    trt_start = f.read(100)
    print("TRT start hex:", trt_start.hex()[:100])
    print("TRT start ASCII:", "".join(chr(b) if 32 <= b <= 126 else "." for b in trt_start))
    
    # Check if this starts with 'trtf' (0x74727466)
    if trt_start.startswith(b'trtf'):
        print("🎉 SUCCESS! It starts with the correct TensorRT magic tag 'trtf'!")
    else:
        print("❌ Does not start with 'trtf'. Starts with:", trt_start[:4])
