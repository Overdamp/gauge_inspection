# คำแนะนำตั้งค่าสภาวะแวดล้อม - ระบบอ่านค่ามิเตอร์เข็มอัตโนมัติ

## 📋 สิ่งที่ต้องเตรียม

ก่อนเริ่ม ตรวจสอบว่ามีของเหล่านี้:
- ✅ Python 3.8 ขึ้นไป (3.9 หรือ 3.10 ดี)
- ✅ pip (โปรแกรมติดตั้ง packages)
- ✅ (ไม่บังคับ) CUDA 11.x ถ้ามี GPU NVIDIA
- ✅ RAM 8 GB ขึ้นไป (16 GB ยิ่งดี)
- ✅ พื้นที่ disk 4 GB

---

## 🔧 ขั้นตอนที่ 1: ตรวจสอบ Python

### Linux / macOS

```bash
# ตรวจสอบเวอร์ชั่น Python
python3 --version

# ผลลัพธ์ที่คาดหวัง: Python 3.8.x ขึ้นไป ✅
# ตัวอย่าง: Python 3.9.13
```

### Windows (ถ้ามี Anaconda)

```bash
# ใน Anaconda Prompt
python --version
```

---

## 📦 ขั้นตอนที่ 2: ติดตั้ง Packages

### ตัวเลือก A: อัตโนมัติ (แนะนำ)

```bash
# ไปยังโฟลเดอร์โปรเจค
cd /home/luke/gauge_inspection

# ติดตั้งจากไฟล์ requirements.txt
pip install -r requirements.txt
```

**เวลา**: 10-15 นาที  
**ขนาด**: ~500 MB  
**ต้องใช้**: เน็ต

### ตัวเลือก B: ติดตั้งแบบสัญลักษณ์

ถ้าตัวเลือก A มีปัญหา ติดตั้งทีละรายการ:

```bash
# Packages หลัก
pip install numpy opencv-python pillow pyyaml

# Deep Learning
pip install torch torchvision

# YOLOv8
pip install ultralytics

# OCR
pip install doctr

# ไม่บังคับ: Jupyter (สำหรับ notebook)
pip install jupyter notebook matplotlib
```

### ตัวเลือก C: ใช้ GPU (NVIDIA)

ถ้ามี NVIDIA GPU:

```bash
# ติดตั้ง PyTorch พร้อม CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# จากนั้นติดตั้ง packages อื่น
pip install -r requirements.txt
```

---

## 🖥️ ขั้นตอนที่ 3: ตรวจสอบ GPU (ถ้ามี)

```bash
# ตรวจสอบว่า CUDA พร้อม
python -c "
import torch
print('GPU พร้อมหรือไม่:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('ชื่อ GPU:', torch.cuda.get_device_name(0))
    print('CUDA Version:', torch.version.cuda)
else:
    print('จะใช้ CPU (ช้ากว่า)')
"
```

**ผลลัพธ์ที่คาดหวัง**:
```
GPU พร้อมหรือไม่: True
ชื่อ GPU: NVIDIA GeForce RTX 3090 (หรือ GPU อื่น)
CUDA Version: 11.8
```

ถ้า GPU ไม่พร้อม ไม่เป็นไร ระบบจะใช้ CPU แทน (แต่ช้าน้อย)

---

## ✅ ขั้นตอนที่ 4: ตรวจสอบการติดตั้ง

### ตรวจสอบทั้งหมด

```bash
# รันโปรแกรมตรวจสอบ
python -c "
import sys
print(f'Python Version: {sys.version}')
print()

packages = {
    'numpy': 'NumPy',
    'cv2': 'OpenCV',
    'PIL': 'Pillow',
    'torch': 'PyTorch',
    'torchvision': 'TorchVision',
    'ultralytics': 'YOLOv8 (ultralytics)',
    'yaml': 'PyYAML',
}

print('ตรวจสอบ Packages ที่ต้อง (Required):')
for pkg_name, display_name in packages.items():
    try:
        mod = __import__(pkg_name)
        version = getattr(mod, '__version__', 'unknown')
        print(f'  ✓ {display_name:30} - {version}')
    except ImportError:
        print(f'  ✗ {display_name:30} - ไม่ติดตั้ง')
"
```

**ผลลัพธ์ที่คาดหวัง**: ทั้งหมด ✓ = สำเร็จ ✅

---

## 🐛 แก้ปัญหาทั่วไป

### ปัญหา 1: "Python not found"

**วิธีแก้**:
```bash
# Linux/macOS - ติดตั้ง Python
# Homebrew (macOS):
brew install python3

# apt (Ubuntu/Debian):
sudo apt-get install python3 python3-pip

# yum (CentOS/RHEL):
sudo yum install python3 python3-pip
```

### ปัญหา 2: "Permission denied"

**วิธีแก้**:
```bash
# วิธี 1: ใช้ --user flag (ปลอดภัยกว่า)
pip install --user -r requirements.txt

# วิธี 2: ใช้ sudo (ไม่แนะนำ)
sudo pip install -r requirements.txt
```

### ปัญหา 3: "pip: command not found"

**วิธีแก้**:
```bash
# ติดตั้ง pip
python3 -m ensurepip --upgrade

# ลองใหม่
pip install -r requirements.txt
```

### ปัญหา 4: "No module named X"

**วิธีแก้**:
```bash
# ติดตั้งใหม่ด้วยพลัง
pip install --force-reinstall <ชื่อ_package>

# ตัวอย่าง:
pip install --force-reinstall numpy
```

### ปัญหา 5: GPU/CUDA ไม่พบ

**วิธีแก้**:
```bash
# ตรวจสอบ NVIDIA
nvidia-smi

# ถ้าไม่เห็น: ลองถอน PyTorch และติดตั้งใหม่
pip uninstall torch torchvision

# ติดตั้งพร้อม CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### ปัญหา 6: Packages ล้าสมัย

**วิธีแก้**:
```bash
# อัปเดตทั้งหมด
pip install --upgrade -r requirements.txt
```

### ปัญหา 7: Conflict ระหว่าง Packages

**วิธีแก้**:
```bash
# สร้าง Virtual Environment (แยก environments)
python -m venv gauge_env

# เข้า virtual environment
# Linux/macOS:
source gauge_env/bin/activate
# Windows:
.\gauge_env\Scripts\activate

# ติดตั้งใหม่
pip install -r requirements.txt
```

---

## 📁 โครงสร้าง Directory หลัง Setup

หลังติดตั้งเสร็จ directory ควรมีลักษณะนี้:

```
gauge_inspection/
├── main.py                    # ไฟล์หลัก
├── requirements.txt           # รายชื่อ packages
├── configs/
│   └── config.yaml           # ไฟล์ตั้งค่า
├── models/                    # โมเดลที่ฝึกไว้
│   └── analog_gauge_model/
├── libs/                      # Source code
├── logs/                      # บันทึก (สร้างอัตโนมัติ)
└── debug_output/              # ผลลัพธ์ debug (สร้างอัตโนมัติ)
```

---

## 🎓 Virtual Environment (แนะนำ)

ใช้ Virtual Environment เพื่อไม่ให้มีปัญหาระหว่าง projects:

```bash
# สร้าง virtual environment
python -m venv gauge_env

# เข้า virtual environment
# Linux/macOS:
source gauge_env/bin/activate
# Windows:
.\gauge_env\Scripts\activate

# ติดตั้ง packages
pip install -r requirements.txt

# หลังทำงานเสร็จ ออกจาก virtual environment:
deactivate
```

---

## 💡 เคล็ดลับ

1. **อัปเดต pip ก่อน**:
   ```bash
   pip install --upgrade pip setuptools wheel
   ```

2. **ตรวจสอบทรัพยากร**:
   ```bash
   # ตรวจสอบ Memory
   free -h  # Linux/macOS
   
   # ตรวจสอบ Disk
   df -h
   
   # ตรวจสอบ GPU
   nvidia-smi
   ```

3. **สร้าง requirements.txt** (ถ้าต้องการส่วนสำหรับคนอื่น):
   ```bash
   pip freeze > requirements.txt
   ```

---

## ✅ Checklist ตรวจสอบให้เสร็จ

- [ ] Python 3.8+ ติดตั้งแล้ว
- [ ] pip ทำงานได้
- [ ] ติดตั้ง packages จากไฟล์ requirements.txt
- [ ] ทั้งหมด packages ใช้ได้ (ตรวจสอบด้วยโปรแกรมที่ให้มา)
- [ ] (ไม่บังคับ) GPU/CUDA พร้อม
- [ ] โฟลเดอร์ models/ มี model files
- [ ] ไฟล์ configs/config.yaml อยู่
- [ ] โฟลเดอร์ logs/ สามารถสร้างได้
- [ ] หน่วยความจำ RAM เพียงพอ (8 GB)
- [ ] พื้นที่ disk เพียงพอ (4 GB)

ถ้าทั้งหมด ✅ คุณพร้อมไปต่อไป!

---

## 🚀 ขั้นตอนต่อไป

ติดตั้งเสร็จแล้ว? ไปที่:

1. **QUICK_START_TH.md** - เริ่มใช้งานเร็ว
2. **USAGE_GUIDE.ipynb** - ขั้นตอนละเอียด
3. **README_TH.md** - คำอธิบายแบบละเอียด

---

**ติดตั้งเสร็จแล้ว? เริ่มใช้งานได้เลย!** 🎉

```bash
python main.py
```
