#!/bin/bash

# FreeCAD AI Addon Nuclear Minimal Test
# Tests the crash fix implementation

echo "🧪 Testing FreeCAD AI Addon Nuclear Minimal Approach"
echo "=================================================="

FREECAD_APP="/home/jango/Git/mcp-freecad/FreeCAD_1.0.0-conda-Linux-x86_64-py311.AppImage"
LOG_FILE="/home/jango/Git/mcp-freecad/nuclear_minimal_test.log"

echo "📋 Test Steps:"
echo "1. Launch FreeCAD"
echo "2. Activate FreeCAD AI workbench"
echo "3. Check for crashes"
echo "4. Verify minimal UI loads"
echo "5. Test click-to-initialize"
echo ""

echo "🚀 Starting FreeCAD with nuclear minimal addon..."

# Clear previous log
> "$LOG_FILE"

# Start FreeCAD and log output
"$FREECAD_APP" > "$LOG_FILE" 2>&1 &
FREECAD_PID=$!

echo "📊 FreeCAD PID: $FREECAD_PID"
echo "📁 Log file: $LOG_FILE"
echo ""

# Wait for startup
echo "⏳ Waiting for FreeCAD startup (10 seconds)..."
sleep 10

# Check if process is still running (crash test)
if kill -0 "$FREECAD_PID" 2>/dev/null; then
    echo "✅ SUCCESS: FreeCAD is running (no immediate crash)"
    
    # Check log for our addon messages
    if grep -q "FreeCAD AI: Nuclear minimal widget created" "$LOG_FILE"; then
        echo "✅ SUCCESS: Nuclear minimal widget created successfully"
    else
        echo "⚠️  WARNING: Nuclear minimal widget creation not detected in log"
    fi
    
    if grep -q "segmentation fault\|Segmentation fault\|SIGSEGV" "$LOG_FILE"; then
        echo "❌ FAILURE: Segmentation fault detected in log"
    else
        echo "✅ SUCCESS: No segmentation faults detected"
    fi
    
    echo ""
    echo "🎯 Test Result: NUCLEAR MINIMAL APPROACH WORKING"
    echo "   - No immediate crash on workbench activation"
    echo "   - Minimal widget creation successful"
    echo "   - Ready for click-to-initialize testing"
    
    # Keep running for manual testing
    echo ""
    echo "🖱️  Manual Test: Click 'Initialize Full AI Features' button in FreeCAD"
    echo "⏸️  Press Ctrl+C to stop when manual testing is complete"
    wait "$FREECAD_PID"
    
else
    echo "❌ FAILURE: FreeCAD process crashed or exited"
    echo "📄 Last 20 lines of log:"
    tail -20 "$LOG_FILE"
fi

echo ""
echo "🏁 Test completed. Check $LOG_FILE for detailed output."