# Quick Start Guide - Analog Gauge Inspection System

## 🚀 Quick Start in 5 Minutes

### Step 1: Install Dependencies (2-3 minutes)

```bash
# Navigate to project directory
cd /home/luke/gauge_inspection

# Install required packages
pip install -r requirements.txt
```

**First time only!** This will install all necessary packages (~500 MB).

---

### Step 2: Run the System

#### Option A: Run Batch Processing (Simple)

```bash
# Process all images in the input folder
python main.py
```

This will:
- ✅ Load all models
- ✅ Process all images in the input folder
- ✅ Generate results and debug visualizations
- ✅ Save output to the results folder

#### Option B: Run Visualizer (View Segmentation)

```bash
# View segmentation results
python visualize.py
```

#### Option C: Use Jupyter Notebook (Interactive)

```bash
# Start Jupyter
jupyter notebook USAGE_GUIDE.ipynb
```

Then follow the step-by-step instructions in the notebook.

---

### Step 3: Check Results

**Output Location**: `/home/engineer00/winworkspace/PTTEP/AnalogGaugeReading/gauge-win-v3/results/`

Files generated:
- `result_*.jpg` - Successful gauge readings with 8-panel debug visualization
- `failed_*.jpg` - Failed attempts with debug information

**Debug Output**: `debug_output/` folder (if debug mode is enabled)

---

## 📊 Configuration

Edit `configs/config.yaml` to customize:

```yaml
# Device (cuda or cpu)
device: "cuda"

# Confidence thresholds
conf: 0.5      # Detection confidence
iou: 0.5       # IoU threshold

# Debug mode
debug:
  enabled: true
  output_dir: "debug_output"
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **CUDA not found** | System will fallback to CPU. Processing will be slower. |
| **Models not loading** | Check `config.yaml` model paths are correct. |
| **No images found** | Verify input folder: `/home/engineer00/winworkspace/PTTEP/Objectdetection/crop_gauge_result/analog-gauge` |
| **Out of memory** | Reduce batch size or image resolution in config. |
| **Processing too slow** | Ensure GPU is being used (check first output line). |

---

## 📚 Documentation

- **PROJECT_OVERVIEW.md** - Full project documentation
- **USAGE_GUIDE.ipynb** - Step-by-step interactive guide
- **WORK_LOG.md** - Development notes
- **config.yaml** - Configuration reference

---

## ⚡ Performance Tips

1. **Use GPU**: System defaults to CUDA. Check if GPU is available:
   ```bash
   python -c "import torch; print(torch.cuda.is_available())"
   ```

2. **Enable Debug Mode**: See detailed 8-panel visualizations
   ```yaml
   debug:
     enabled: true
   ```

3. **Adjust Thresholds**: If getting too many false positives/negatives:
   ```yaml
   conf: 0.6    # Increase to be more strict
   ```

---

## 🎯 Expected Results

For a typical gauge image:
- **Processing time**: 2-5 seconds per image (GPU) / 10-30 seconds (CPU)
- **Output**: Gauge reading value (e.g., "45.5 PSI")
- **Quality score**: R² value (0-1, higher is better)
- **Debug visualization**: 8-panel image showing processing steps

---

## 📞 Support

If you encounter issues:

1. Check the console output for error messages
2. Review the debug visualizations in the output folder
3. Check `logs/analog_system.log` for detailed logs
4. Refer to PROJECT_OVERVIEW.md for technical details
5. Run USAGE_GUIDE.ipynb for step-by-step troubleshooting

---

**Ready to start?** Run this command:
```bash
cd /home/luke/gauge_inspection && python main.py
```

Happy gauge reading! 📈
