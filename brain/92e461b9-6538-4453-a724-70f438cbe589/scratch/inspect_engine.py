import struct

with open("models/analog_gauge_model/segmentation/best_segment_v2.engine", "rb") as f:
    header = f.read(100)
    print("Header bytes (hex):", header.hex()[:100])
    # Let's see if we can find the magic bytes 'TRT' or 'trtf' in the header
    print("Header ASCII representation:", "".join(chr(b) if 32 <= b <= 126 else "." for b in header))
    
    # Let's search for the magic tag 'trtf' (0x74727466) in the file
    f.seek(0)
    data = f.read()
    magic_pos = data.find(b'trtf')
    print("Position of 'trtf':", magic_pos)
