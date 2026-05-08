# เริ่มต้นใช้งาน - ระบบอ่านค่ามิเตอร์เข็มอัตโนมัติ

## 🚀 เริ่มใช้งานใน 5 นาที

### ขั้นตอนที่ 1: ติดตั้ง Packages (2-3 นาที)

```bash
# ไปยังโฟลเดอร์โปรเจค
cd /home/luke/gauge_inspection

# ติดตั้ง packages ที่จำเป็น
pip install -r requirements.txt
```

**ครั้งแรกเท่านั้น!** จะดาวน์โหลดประมาณ 500 MB

---

### ขั้นตอนที่ 2: รัน (ใช้งาน) ระบบ

#### ตัวเลือก A: ประมวลผล Batch (แนะนำ)

```bash
# ประมวลผลภาพทั้งหมดในโฟลเดอร์ input
python main.py
```

ระบบจะ:
- ✅ โหลด models ทั้งหมด
- ✅ ประมวลผลทุกรูป
- ✅ สร้างภาพ debug (รายงาน 8 ส่วน)
- ✅ บันทึกผลลัพธ์

#### ตัวเลือก B: ดูผลแบ่งส่วน

```bash
# ดูภาพแบ่งส่วน (segmentation)
python visualize.py
```

#### ตัวเลือก C: ใช้ Jupyter Notebook (ขั้นต่อเดียว)

```bash
# เปิด Notebook
jupyter notebook USAGE_GUIDE.ipynb
```

จากนั้นทำตามขั้นตอนในแต่ละเซลล์

---

### ขั้นตอนที่ 3: ตรวจสอบผลลัพธ์

**ที่เก็บผลลัพธ์**: `/home/engineer00/winworkspace/PTTEP/AnalogGaugeReading/gauge-win-v3/results/`

ไฟล์ที่สร้าง:
- `result_*.jpg` - ภาพ debug (สำเร็จ) - แสดงกระบวนการ 8 ส่วน
- `failed_*.jpg` - ภาพ debug (ล้มเหลว) - เพื่อหาเหตุผล

**Debug Output**: โฟลเดอร์ `debug_output/` (ถ้าเปิด debug mode)

---

## 📊 ตั้งค่า Config

แก้ไขไฟล์ `configs/config.yaml` เพื่อปรับแต่ง:

```yaml
# ใช้ GPU หรือ CPU
device: "cuda"         # "cuda" = ใช้ GPU, "cpu" = ใช้ CPU

# ค่า Thresholds
conf: 0.5              # ความเชื่อมั่น (0-1 ยิ่งสูงยิ่งเคร่งเคียว)
iou: 0.5               # ค่าเปรียบเทียบ

# Debug mode
debug:
  enabled: true        # true = เปิด debug, false = ปิด
  output_dir: "debug_output"  # โฟลเดอร์เก็บภาพ
```

---

## 🐛 แก้ปัญหา

| ปัญหา | วิธีแก้ |
|-------|--------|
| **CUDA ไม่พบ** | ระบบจะใช้ CPU แทน (ช้ากว่า) |
| **โมเดลไม่โหลด** | ตรวจสอบ path ใน config.yaml |
| **ไม่เห็นรูป** | ตรวจสอบโฟลเดอร์ input: `/home/engineer00/...` |
| **หน่วยความจำเต็ม** | ลดขนาดรูปหรือจำนวนรูปต่อครั้ง |
| **ช้ามาก** | ตรวจสอบว่าใช้ GPU ถูกต้อง |

---

## 📚 เอกสาร

- **README_TH.md** - คำอธิบายเต็มของโปรเจค (ภาษาไทย)
- **PROJECT_OVERVIEW.md** - คำอธิบายเต็ม (ภาษาอังกฤษ)
- **USAGE_GUIDE.ipynb** - ไฟล์ Jupyter สำหรับปฏิบัติ
- **ENVIRONMENT_SETUP.md** - วิธีตั้งค่า (ภาษาอังกฤษ)
- **ENVIRONMENT_SETUP_TH.md** - วิธีตั้งค่า (ภาษาไทย)
- **config.yaml** - ไฟล์ตั้งค่า

---

## ⚡ เคล็ดลับเร่งความเร็ว

1. **ใช้ GPU**: ระบบใช้ CUDA โดยอัตโนมัติ ตรวจสอบ:
   ```bash
   python -c "import torch; print(torch.cuda.is_available())"
   ```
   ผลลัพธ์ `True` = มี GPU ✅

2. **เปิด Debug Mode**: ดูภาพรายงาน 8 ส่วน
   ```yaml
   debug:
     enabled: true
   ```

3. **ปรับค่า Confidence**: ถ้าอ่านผิดบ่อย:
   ```yaml
   conf: 0.6    # สูงขึ้น = เคร่งเคียวมากขึ้น
   ```

---

## 🎯 ผลลัพธ์ที่คาดหวัง

สำหรับรูปมิเตอร์ทั่วไป:
- **เวลาประมวลผล**: 2-5 วินาที/รูป (GPU) หรือ 10-30 วินาที/รูป (CPU)
- **ผลลัพธ์**: ค่ามิเตอร์ (เช่น "45.5 PSI")
- **คะแนนคุณภาพ**: R² value (0-1 ยิ่งสูงยิ่งดี)
- **ภาพ Debug**: 8 ส่วน แสดงขั้นตอนการประมวลผล

---

## 📞 การสนับสนุน

ถ้ามีปัญหา:

1. ตรวจสอบ message ในคอนโซล
2. ดูภาพ debug ในโฟลเดอร์ output
3. ตรวจสอบ `logs/analog_system.log` (ไฟล์บันทึก)
4. อ่าน README_TH.md (คำอธิบายละเอียด)
5. รัน USAGE_GUIDE.ipynb (ขั้นตอนละเอียด)

---

## 🎓 ตัวอย่าง Output Log

```
=== Starting Analog Gauge Batch Inference ===
[DEBUG MODE ON] Reports will be saved to: debug_output
Initializing Analog Gauge Models...
Models loaded successfully.
Found 5 images to process.

Processing: gauge_1.jpg ...
-> Result [gauge_1.jpg]: 45.50 PSI (R2: 0.95)

Processing: gauge_2.jpg ...
-> Result [gauge_2.jpg]: 120.30 BAR (R2: 0.92)

Processing: gauge_3.jpg ...
-> Failed to calculate gauge value for: gauge_3.jpg

=== Inference Completed ===
Successfully processed 2/3 images in 12.45 seconds.
Results saved to '/home/engineer00/...results' directory.
✓ Debug reports for ALL images saved to: debug_output directory.
```

---

**พร้อมเริ่มแล้ว?** รันคำสั่งนี้:
```bash
cd /home/luke/gauge_inspection && python main.py
```

ขอให้ประมวลผลสำเร็จ! 📈
