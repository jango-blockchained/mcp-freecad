# Live House Modeling Test Runners 🏠

This directory contains multiple approaches to demonstrate the MCP-FreeCAD house modeling capabilities on a **real FreeCAD instance with GUI**, allowing you to watch the 3D house being built step by step in real-time!

## ⚠️ Important: Original Scripts Had Issues

The original `run_live_house_test.py` and `run_live_house_test_mcp.py` scripts had problems trying to import FreeCAD modules directly from outside FreeCAD. I've created **fixed versions** that work properly!

## 🛠️ Working Solutions

### **🎯 Option 1: Simple Macro Approach (RECOMMENDED)** 

**File:** `run_house_macro.py` + `house_modeling_macro.FCMacro`

This is the **most reliable method** - it runs FreeCAD with a macro that executes inside FreeCAD's environment where all modules are available.

```bash
# Simple and reliable!
python run_house_macro.py
```

**What happens:**
1. 🚀 Starts FreeCAD with GUI automatically
2. 📜 Runs the house modeling macro inside FreeCAD
3. 🏗️ Builds the house step-by-step with 2-second delays
4. 🔍 Leaves FreeCAD open for inspection

### **🎯 Option 2: Fixed MCP Connection Approach**

**File:** `run_live_house_test_fixed.py`

This uses the proper MCP-FreeCAD connection architecture without trying to import FreeCAD directly.

```bash
# Fixed MCP approach
python run_live_house_test_fixed.py
```

**What happens:**
1. 🚀 Starts FreeCAD as separate process
2. 🔗 Establishes MCP connection to FreeCAD
3. 📡 Sends commands to FreeCAD via connection manager
4. 🏗️ Builds house using proper MCP workflow

## 🏠 What These Tests Build

Both approaches create the same house model:

1. **🏗️ Foundation** - 10m × 8m × 0.3m concrete slab (brown)
2. **🧱 Four Walls** - 3m high, 0.3m thick brick walls (red)
3. **🪟 Two Windows** - 1.2m × 1.5m front windows (blue transparent)
4. **🚪 One Door** - 0.9m × 2.1m front door (blue transparent)

## 🚀 Usage Examples

### Basic Usage:
```bash
# Recommended - simple and reliable
python run_house_macro.py

# Fixed MCP approach (more complex)
python run_live_house_test_fixed.py
```

### Custom Timing:
```bash
# For macro approach - edit STEP_DELAY in house_modeling_macro.FCMacro
# Then run:
python run_house_macro.py

# For MCP approach - use delay parameter
python run_live_house_test_fixed.py --delay 1.0   # Fast (1s steps)
python run_live_house_test_fixed.py --delay 5.0   # Slow (5s steps)
```

### Direct FreeCAD Macro:
```bash
# Run macro directly in FreeCAD
./FreeCAD_1.0.0-conda-Linux-x86_64-py311.AppImage --run-macro house_modeling_macro.FCMacro
```

## 🔧 Requirements

- **FreeCAD AppImage** must be in project root: `FreeCAD_1.0.0-conda-Linux-x86_64-py311.AppImage`
- **Python environment** with MCP-FreeCAD dependencies (for MCP approach)
- **GUI environment** (X11/Wayland) for visual display

## 🎬 What You'll See

When running either test, you'll watch:

1. **🚀 FreeCAD starting** with splash screen
2. **📄 New document creation** 
3. **🏗️ Foundation appearing** (brown rectangular base)
4. **🧱 Walls rising** one by one (red brick walls)
5. **🪟 Windows appearing** (blue transparent openings)
6. **🚪 Door being cut** (blue transparent opening)
7. **🎨 Final view adjustment** (isometric view, fit all)

Each step has a delay (default 2 seconds) so you can follow the construction process!

## 🐛 Troubleshooting

### Error: "No module named 'FreeCAD'"
- **Solution:** Use `run_house_macro.py` (recommended) or the fixed MCP version
- **Cause:** Original scripts tried to import FreeCAD from outside FreeCAD

### Error: "FreeCAD AppImage not found"
- **Solution:** Ensure `FreeCAD_1.0.0-conda-Linux-x86_64-py311.AppImage` is in project root
- **Check:** `ls -la FreeCAD_*.AppImage`

### Error: Connection issues (MCP approach)
- **Solution:** Try the macro approach instead: `python run_house_macro.py`
- **Alternative:** Check FreeCAD is properly started before connection attempts

### FreeCAD doesn't show GUI
- **Solution:** Ensure you're in a GUI environment (not headless SSH)
- **Check:** Try `echo $DISPLAY` - should show something like `:0`

## 📊 Comparison

| Approach | Reliability | Setup Complexity | MCP Demo Value |
|----------|-------------|------------------|----------------|
| **Macro** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Fixed MCP** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**Recommendation:** Start with the **macro approach** for reliability, then try the **MCP approach** to see the full connection architecture in action!

## 🎯 Next Steps

After running the live house test:

1. **🔍 Inspect the model** - Rotate, zoom, explore the 3D house
2. **✏️ Modify objects** - Try changing dimensions in the tree view
3. **💾 Export the model** - Save as STL, STEP, or other formats
4. **🔧 Modify the code** - Customize house dimensions, add rooms, etc.
5. **🚀 Build your own tests** - Use this as a template for other models!
