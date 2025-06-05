# Live House Modeling Test Runners 🏠

This directory contains two test runners that demonstrate the MCP-FreeCAD house modeling capabilities on a **real FreeCAD instance with GUI**, allowing you to watch the 3D house being built step by step in real-time!

## What These Tests Do

These runners execute the same house modeling test that runs in the test suite, but instead of using mock FreeCAD, they:

1. **Start FreeCAD with GUI** using the AppImage
2. **Connect to the real FreeCAD instance** 
3. **Create a 3D house model step by step:**
   - 🏗️ Foundation (10m × 8m × 0.3m concrete slab)
   - 🧱 Four walls (3m high, 0.3m thick brick walls)
   - 🪟 Two front windows (1.2m × 1.5m)
   - 🚪 One front door (0.9m × 2.1m)
4. **Keep FreeCAD open** for you to inspect the model

## Available Test Runners

### 1. `run_live_house_test.py` - Direct Tool Approach
Uses the primitive and model manipulation tool providers directly.

### 2. `run_live_house_test_mcp.py` - Full MCP Architecture  
Uses the complete MCP-FreeCAD server architecture with connection manager.

## Usage

### Basic Usage (2-second delay between steps):
```bash
# Direct tool approach
python run_live_house_test.py

# Full MCP architecture approach  
python run_live_house_test_mcp.py
```

### Custom Timing:
```bash
# Fast demo (1 second between steps)
python run_live_house_test.py --delay 1.0

# Slow demo (5 seconds between steps for detailed viewing)
python run_live_house_test.py --delay 5.0

# Very slow demo (10 seconds - great for presentations)
python run_live_house_test_mcp.py --delay 10.0
```

### With Virtual Environment:
```bash
# Activate the virtual environment first
source venv/bin/activate

# Then run the test
python run_live_house_test.py --delay 3.0
```

## What You'll See

1. **FreeCAD GUI opens** with the startup screen
2. **Foundation appears** as a flat rectangular slab
3. **Walls are created one by one:**
   - Front wall appears and moves into position
   - Back wall appears and moves into position  
   - Left wall appears and moves into position
   - Right wall appears and moves into position
4. **Window and door openings** are created (they appear as cut-out boxes)
5. **Test completes** - FreeCAD remains open for inspection

## Interactive Features

- **Rotate the view** in FreeCAD to see the house from different angles
- **Zoom in/out** to inspect details
- **Use the tree view** to see all created objects
- **Modify objects** if you want to experiment
- **Press Ctrl+C** in the terminal to exit and close FreeCAD

## Troubleshooting

### FreeCAD doesn't start:
- Ensure the AppImage exists: `ls -la FreeCAD_1.0.0-conda-Linux-x86_64-py311.AppImage`
- Make sure it's executable: `chmod +x FreeCAD_1.0.0-conda-Linux-x86_64-py311.AppImage`

### Connection issues:
- Try the alternative runner if one doesn't work
- Check that no other FreeCAD instance is running
- Wait a bit longer for FreeCAD to fully start

### Import errors:
- Activate the virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

## Technical Details

### House Specifications:
- **Foundation:** 10m × 8m × 0.3m concrete slab
- **Walls:** 3m high, 0.3m thick brick construction
- **Windows:** 2 front windows, 1.2m × 1.5m each
- **Door:** 1 front door, 0.9m × 2.1m
- **Total objects created:** ~8 objects (foundation + 4 walls + 2 windows + 1 door)

### Architecture Differences:
- **Direct approach:** Uses tool providers directly, simpler but less realistic
- **MCP approach:** Uses full server architecture, more realistic to actual MCP usage

### Performance:
- **Startup time:** ~8-10 seconds (FreeCAD loading)
- **Modeling time:** ~15-30 seconds (depending on delay setting)
- **Total time:** ~30-45 seconds for complete demo

## Educational Value

These tests demonstrate:
- ✅ **Real-world MCP-FreeCAD integration**
- ✅ **Step-by-step 3D modeling workflow**
- ✅ **Tool chaining and sequencing**
- ✅ **GUI interaction with programmatic control**
- ✅ **Error handling in live environment**
- ✅ **Performance characteristics**

Perfect for:
- 🎯 **Demonstrations and presentations**
- 🎯 **Learning the MCP-FreeCAD workflow**
- 🎯 **Testing tool integration**
- 🎯 **Debugging modeling sequences**
- 🎯 **Validating real-world performance**

## Next Steps

After running these tests, you can:
- Modify the house specifications in the code
- Add more complex features (roof, stairs, etc.)
- Experiment with different materials and textures
- Use the created model as a starting point for your own designs
- Integrate these patterns into your own MCP-FreeCAD applications

Enjoy watching your house come to life! 🏠✨ 
