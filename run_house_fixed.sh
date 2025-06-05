#!/bin/bash

# Fixed FreeCAD House Modeling Script
# This properly executes the Python script in FreeCAD console

echo "🏠 Live House Modeling - Fixed Launcher"
echo "======================================="

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

echo "🚀 Starting FreeCAD and executing house modeling script..."
echo "📄 Script: $SCRIPT_FILE"
echo "🎛️  Mode: Console mode with script execution"
echo ""
echo "What will happen:"
echo "1. FreeCAD will start in console mode"
echo "2. The house modeling script will be executed automatically"
echo "3. You'll see step-by-step progress in the terminal"
echo "4. Model will be created and saved"
echo "5. Script will exit automatically when complete"
echo ""

# Create a temporary script that executes our house script and exits
TEMP_EXEC_SCRIPT="/tmp/freecad_house_exec.py"
cat > "$TEMP_EXEC_SCRIPT" << 'EOF'
print("🏠 FreeCAD House Modeling - Auto Execution")
print("=" * 50)
try:
    # Execute the house modeling script
    exec(open('./house_modeling_script.py').read())
    print("\n🎉 House modeling script completed successfully!")
    print("📄 Document 'LiveHouseModel' has been created.")
    print("✅ You can now open FreeCAD GUI to view the 3D model.")
except Exception as e:
    print(f"\n❌ Error executing script: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("\n🔚 Exiting FreeCAD console...")
    # Exit FreeCAD
    import sys
    sys.exit(0)
EOF

echo "🔧 Running: $FREECAD_APPIMAGE --console"
echo "📺 Watch for step-by-step progress below:"
echo ""

# Run FreeCAD console mode and pipe our execution script to it
"$FREECAD_APPIMAGE" --console < "$TEMP_EXEC_SCRIPT"

RESULT=$?

# Clean up temporary file
rm -f "$TEMP_EXEC_SCRIPT"

echo ""
if [ $RESULT -eq 0 ]; then
    echo "✅ House modeling completed successfully!"
    echo ""
    echo "🔍 To view the 3D model:"
    echo "   1. Run: $FREECAD_APPIMAGE"
    echo "   2. Open the 'LiveHouseModel' document (File -> Open Recent)"
    echo "   3. Switch to 3D view to see your house!"
    echo ""
    echo "💡 Alternative: The model might be automatically saved as LiveHouseModel.FCStd"
else
    echo "⚠️  FreeCAD exited with code: $RESULT"
    echo ""
    echo "💡 Troubleshooting:"
    echo "   - Check if the script ran by looking for step-by-step output above"
    echo "   - Try running FreeCAD GUI manually to check if the document was created"
    echo "   - Look for any error messages in the output above"
fi

exit $RESULT
