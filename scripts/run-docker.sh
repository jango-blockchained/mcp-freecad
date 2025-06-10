#!/bin/bash

# FreeCad Docker Runner - Easy setup script
# Allows users to easily choose between different FreeCad installation methods

set -e

echo "🚀 FreeCad Docker Setup"
echo "========================"
echo ""

# Function to show usage
show_usage() {
    echo "Usage: $0 [METHOD]"
    echo ""
    echo "Methods:"
    echo "  download  - Download AppImage in container (default)"
    echo "  external  - Use external AppImage from host"
    echo "  apt       - Use FreeCad installed via apt"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 download"
    echo "  $0 external"
    echo "  $0 apt"
    echo ""
}

# Function to run download method
run_download() {
    echo "📦 Using Download AppImage method"
    echo "This will download the latest FreeCad AppImage during build..."
    echo ""
    docker-compose --profile download up --build
}

# Function to run external method
run_external() {
    echo "🔗 Using External AppImage method"
    echo "Checking for existing AppImage..."

    # Check if AppImage exists
    if ls FreeCAD*.AppImage 1> /dev/null 2>&1; then
        echo "✅ Found existing AppImage(s):"
        ls -la FreeCAD*.AppImage
        echo ""
    else
        echo "❌ No FreeCad AppImage found in current directory"
        echo ""
        read -p "Do you want to download one now? (y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "📥 Downloading FreeCad AppImage..."
            ./download.sh
        else
            echo "❌ External method requires a FreeCad AppImage"
            echo "   Download one manually or use: ./download.sh"
            exit 1
        fi
    fi

    echo "🐳 Starting container with external AppImage..."
    docker-compose --profile external up --build
}

# Function to run apt method
run_apt() {
    echo "📦 Using APT installation method"
    echo "This will install FreeCad via Ubuntu package manager..."
    echo ""
    docker-compose --profile apt up --build
}

# Function to choose interactively
interactive_choice() {
    echo "Choose FreeCad installation method:"
    echo ""
    echo "1) Download AppImage (latest version, slower build)"
    echo "2) External AppImage (use your own, faster build)"
    echo "3) APT Install (system package, fastest build)"
    echo ""
    read -p "Enter your choice [1-3]: " -n 1 -r
    echo ""
    echo ""

    case $REPLY in
        1)
            run_download
            ;;
        2)
            run_external
            ;;
        3)
            run_apt
            ;;
        *)
            echo "❌ Invalid choice. Please select 1, 2, or 3."
            exit 1
            ;;
    esac
}

# Main logic
case "${1:-}" in
    "download"|"")
        run_download
        ;;
    "external")
        run_external
        ;;
    "apt")
        run_apt
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        echo "❌ Unknown method: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
