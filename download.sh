#!/bin/bash

# FreeCad AppImage Downloader for Ubuntu
# Downloads the latest FreeCad AppImage for Linux x86_64

set -e  # Exit on any error

echo "🚀 FreeCad AppImage Downloader"
echo "================================"

# Configuration
GITHUB_API_URL="https://api.github.com/repos/FreeCAD/FreeCAD/releases/latest"
DOWNLOAD_DIR="$(pwd)"
APPIMAGE_PATTERN="FreeCAD.*Linux.*x86_64.*AppImage$"

echo "📡 Fetching latest FreeCad release information..."

# Get the latest release information from GitHub API
RELEASE_INFO=$(curl -s "$GITHUB_API_URL")

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to fetch release information from GitHub API"
    exit 1
fi

# Extract download URL for Linux AppImage
DOWNLOAD_URL=$(echo "$RELEASE_INFO" | grep -o '"browser_download_url": *"[^"]*"' | grep -E "$APPIMAGE_PATTERN" | head -1 | cut -d'"' -f4)

if [ -z "$DOWNLOAD_URL" ]; then
    echo "❌ Error: Could not find FreeCad AppImage download URL"
    echo "Available assets:"
    echo "$RELEASE_INFO" | grep -o '"name": *"[^"]*"' | cut -d'"' -f4
    exit 1
fi

# Extract filename from URL
FILENAME=$(basename "$DOWNLOAD_URL")
FILEPATH="$DOWNLOAD_DIR/$FILENAME"

echo "📦 Found FreeCad AppImage: $FILENAME"
echo "🔗 Download URL: $DOWNLOAD_URL"

# Check if file already exists
if [ -f "$FILEPATH" ]; then
    echo "✅ FreeCad AppImage already exists: $FILEPATH"
    echo "🔄 Skipping download. Delete the file to re-download."
    echo "📍 AppImage location: $FILEPATH"
    exit 0
fi

# Download the AppImage
echo "⬇️  Downloading FreeCad AppImage..."
curl -L -o "$FILEPATH" "$DOWNLOAD_URL"

if [ $? -eq 0 ]; then
    echo "✅ Download completed successfully!"

    # Make the AppImage executable
    chmod +x "$FILEPATH"
    echo "🔧 Made AppImage executable"

    echo "📍 AppImage saved to: $FILEPATH"
    echo "🎉 FreeCad AppImage is ready to use!"

    # Display file info
    echo ""
    echo "📊 File Information:"
    ls -lh "$FILEPATH"

else
    echo "❌ Error: Download failed"
    exit 1
fi

echo ""
echo "🐳 To use with Docker, the AppImage will be automatically integrated"
echo "   when you run: docker-compose up --build"
