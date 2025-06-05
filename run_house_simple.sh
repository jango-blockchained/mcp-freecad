#!/bin/bash

# Simple FreeCAD House Modeling Launcher Script
# This handles Qt platform issues and runs the house modeling script

echo "🏠 Live House Modeling - Simple Launcher"
echo "========================================"

# Set Qt platform to X11 to avoid Wayland issues
export QT_QPA_PLATFORM=xcb

# Check if FreeCAD AppImage exists
FREECAD_APPIMAGE="./FreeCAD_1.0.0-conda-Linux-x86_64-py311.AppImage"
SCRIPT_FILE="./house_modeling_script.py"

if [ ! -f "$FREECAD_APPIMAGE" ]; then
    echo "❌ FreeCAD AppImage not found: $FREECAD_APPIMAGE"
    echo "Please ensure the FreeCAD AppImage is in the project root directory."
    exit 1
fi

if [ ! -f "$SCRIPT_FILE" ]; then
    echo "❌ Script file not found: $SCRIPT_FILE"
    echo "Please ensure the house_modeling_script.py file exists."
    exit 1
fi

# Make AppImage executable
chmod +x "$FREECAD_APPIMAGE"

echo "🚀 Starting FreeCAD with house modeling script..."
echo "📄 Script: $SCRIPT_FILE"
echo "🎛️  Mode: Console mode with Qt X11 backend"
echo ""
echo "What will happen:"
echo "1. FreeCAD will start in console mode"
echo "2. The house modeling script will run automatically"
echo "3. You'll see step-by-step progress in the terminal"
echo "4. Model will be saved in FreeCAD"
echo "5. You can open FreeCAD GUI separately to view the model"
echo ""

# Run FreeCAD with console mode and script
echo "🔧 Running: $FREECAD_APPIMAGE --console $SCRIPT_FILE"
echo "📺 Watch for step-by-step progress below:"
echo ""

"$FREECAD_APPIMAGE" --console "$SCRIPT_FILE"

RESULT=$?

echo ""
if [ $RESULT -eq 0 ]; then
    echo "✅ House modeling completed successfully!"
    echo ""
    echo "🔍 To view the 3D model:"
    echo "   1. Run: $FREECAD_APPIMAGE"
    echo "   2. Open the 'LiveHouseModel' document"
    echo "   3. Switch to 3D view to see your house!"
else
    echo "⚠️  FreeCAD exited with code: $RESULT"
fi

exit $RESULT
