# Environment Setup Guide - Analog Gauge Inspection System

## 📋 Prerequisites

Before starting, ensure you have:
- ✅ Python 3.8+ installed
- ✅ pip (Python package manager)
- ✅ (Optional) CUDA 11.x for GPU support
- ✅ 8 GB RAM minimum (16 GB recommended)
- ✅ 4 GB free disk space

---

## 🔧 Step 1: Check Python Installation

### Linux / macOS

```bash
# Check Python version
python3 --version

# If Python 3.8+, you're good!
# Expected output: Python 3.8.x or higher
```

### Windows (Anaconda)

```bash
# In Anaconda Prompt
python --version
```

---

## 📦 Step 2: Install Dependencies

### Option A: Automatic Installation (Recommended)

```bash
# Navigate to project directory
cd /home/luke/gauge_inspection

# Install from requirements.txt
pip install -r requirements.txt
```

**Time required**: 10-15 minutes
**Size**: ~500 MB
**Internet**: Required

### Option B: Manual Installation

If `requirements.txt` has issues, install manually:

```bash
# Core packages
pip install numpy opencv-python pillow pyyaml

# Deep Learning
pip install torch torchvision

# YOLOv8
pip install ultralytics

# OCR
pip install doctr

# Optional: Jupyter for notebooks
pip install jupyter notebook matplotlib
```

### Option C: GPU Support (NVIDIA)

If you have an NVIDIA GPU:

```bash
# Install PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Then install other packages
pip install -r requirements.txt
```

---

## 🖥️ Step 3: Verify GPU Availability

```bash
# Check if CUDA is available
python -c "import torch; print('GPU Available:', torch.cuda.is_available()); print('GPU Name:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None')"
```

**Expected output:**
```
GPU Available: True
GPU Name: NVIDIA GeForce RTX 3090 (or your GPU model)
```

**If GPU is not available**, the system will automatically use CPU (slower but still works).

---

## ✅ Step 4: Verify Installation

### Check All Packages

```bash
# Run verification script
python -c "
import sys
print(f'Python Version: {sys.version}')

packages = ['numpy', 'cv2', 'PIL', 'torch', 'torchvision', 'ultralytics', 'yaml', 'doctr']
for pkg in packages:
    try:
        __import__(pkg)
        print(f'✓ {pkg} installed')
    except ImportError:
        print(f'✗ {pkg} NOT installed')
"
```

### Expected Output

```
Python Version: 3.8.x ...
✓ numpy installed
✓ cv2 installed
✓ PIL installed
✓ torch installed
✓ torchvision installed
✓ ultralytics installed
✓ yaml installed
✓ doctr installed
```

If all checks pass, you're ready to go! ✅

---

## 🐛 Troubleshooting

### Issue: "Python not found" or "python3 not found"

**Solution**:
```bash
# Linux/macOS - Install Python
# Using Homebrew (macOS):
brew install python3

# Using apt (Ubuntu/Debian):
sudo apt-get install python3 python3-pip

# Using yum (CentOS/RHEL):
sudo yum install python3 python3-pip
```

### Issue: "Permission denied" when installing

**Solution**:
```bash
# Use --user flag
pip install --user -r requirements.txt

# Or use sudo (not recommended)
sudo pip install -r requirements.txt
```

### Issue: "pip: command not found"

**Solution**:
```bash
# Install pip
python3 -m ensurepip --upgrade

# Then try again
pip install -r requirements.txt
```

### Issue: "No module named X"

**Solution**:
```bash
# Reinstall the package
pip install --force-reinstall <package_name>

# Or upgrade all packages
pip install --upgrade -r requirements.txt
```

### Issue: CUDA/GPU issues

**Solution**:
```bash
# Check CUDA installation
nvidia-smi

# If not available, uninstall and reinstall PyTorch
pip uninstall torch torchvision
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

## 📁 Directory Structure

After setup, your directory should look like:

```
gauge_inspection/
├── main.py                    # Main script
├── visualize.py               # Visualization
├── requirements.txt           # Package list
├── configs/
│   └── config.yaml           # Configuration
├── models/                    # Pre-trained models
│   └── analog_gauge_model/
├── libs/                      # Source code
├── logs/                      # Log files (created at runtime)
└── debug_output/              # Debug files (created at runtime)
```

---

## 🚀 Next Steps

1. ✅ Complete environment setup (this guide)
2. ✅ Read QUICK_START.md for basic usage
3. ✅ Run USAGE_GUIDE.ipynb for step-by-step instructions
4. ✅ Check PROJECT_OVERVIEW.md for detailed documentation

---

## 🎓 Development Environment (Optional)

For advanced development:

```bash
# Install dev tools
pip install pytest pytest-cov black flake8 mypy

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate   # Windows
```

---

## 💡 Tips

1. **Virtual Environment** (Recommended):
   ```bash
   python -m venv gauge_env
   source gauge_env/bin/activate  # Linux/macOS
   pip install -r requirements.txt
   ```

2. **Update pip**:
   ```bash
   pip install --upgrade pip setuptools wheel
   ```

3. **Check System Resources**:
   ```bash
   # Linux/macOS
   free -h  # Memory
   df -h    # Disk
   nvidia-smi  # GPU (if available)
   ```

4. **Upgrade Packages**:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

---

## ✅ Verification Checklist

- [ ] Python 3.8+ installed
- [ ] pip working
- [ ] All packages from requirements.txt installed
- [ ] All package imports successful
- [ ] (Optional) GPU/CUDA available
- [ ] Model files exist in `models/` directory
- [ ] Configuration file at `configs/config.yaml`
- [ ] `logs/` directory exists or will be created

---

**If all checks pass, you're ready to use the Analog Gauge Inspection System!** 🎉

Proceed to [QUICK_START.md](QUICK_START.md) to start processing images.
