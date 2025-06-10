# FreeCad Docker Installation Options

This project supports multiple ways to use FreeCad within Docker containers. Choose the method that best fits your needs.

## 🔧 Available Options

### 1. **Download AppImage** (Default)
Downloads the latest FreeCad AppImage automatically during container build.

**Pros:**
- Always gets the latest FreeCad version
- No manual setup required
- Self-contained

**Cons:**
- Longer build time
- Requires internet during build
- Larger image size

**Usage:**
```bash
# Default behavior
docker-compose up --build

# Or explicitly
docker-compose --profile download up --build
```

### 2. **External AppImage**
Use your own pre-downloaded FreeCad AppImage mounted from the host.

**Pros:**
- Control over FreeCad version
- Faster builds (no download)
- Can use custom or modified AppImages

**Cons:**
- Manual AppImage management
- Need to download AppImage separately

**Setup:**
1. Download FreeCad AppImage manually:
   ```bash
   ./download.sh
   # Or download from https://github.com/FreeCAD/FreeCAD/releases
   ```

2. Run with external profile:
   ```bash
   docker-compose --profile external up --build
   ```

**Note:** The docker-compose.yml expects the AppImage to match pattern `FreeCAD*.AppImage` in the project root.

### 3. **APT Installation**
Install FreeCad via Ubuntu's package manager (apt).

**Pros:**
- Smallest image size
- Fast build
- System integration
- No AppImage dependencies

**Cons:**
- May not be the latest FreeCad version
- Limited to Ubuntu repository version

**Usage:**
```bash
docker-compose --profile apt up --build
```

## 🚀 Quick Start Examples

### Default (Download AppImage)
```bash
git clone <your-repo>
cd mcp-freecad
docker-compose up --build
```

### Using Your Own AppImage
```bash
# Download FreeCad AppImage
wget https://github.com/FreeCAD/FreeCAD/releases/download/0.21.2/FreeCAD_0.21.2-Linux-x86_64.AppImage

# Run with external AppImage
docker-compose --profile external up --build
```

### Using APT FreeCad
```bash
docker-compose --profile apt up --build
```

## 🔍 Environment Variables

The following environment variables control FreeCad behavior:

| Variable | Description | Default |
|----------|-------------|---------|
| `FREECAD_INSTALL_METHOD` | Installation method: `download`, `external`, `apt` | `download` |
| `FREECAD_APPIMAGE_PATH` | Path to AppImage (for AppImage methods) | `/app` |
| `APPIMAGE_EXTRACT_AND_RUN` | Extract AppImage before running (performance) | `1` |
| `QT_QPA_PLATFORM` | Qt platform for headless operation | `offscreen` |
| `FREECAD_CONSOLE` | Enable console mode | `1` |

## 🛠️ Build Arguments

You can also build custom images with specific installation methods:

```bash
# Build with download method
docker build --build-arg FREECAD_INSTALL_METHOD=download -t mcp-freecad:download .

# Build with apt method
docker build --build-arg FREECAD_INSTALL_METHOD=apt -t mcp-freecad:apt .

# Build with external method
docker build --build-arg FREECAD_INSTALL_METHOD=external -t mcp-freecad:external .
```

## 📦 Custom AppImage

To use a specific FreeCad AppImage:

1. Place your AppImage in the project root
2. Ensure it's named with pattern `FreeCAD*.AppImage`
3. Make it executable: `chmod +x FreeCAD*.AppImage`
4. Use the external profile: `docker-compose --profile external up`

## 🐛 Troubleshooting

### AppImage Issues
- Ensure the host supports FUSE
- Check AppImage permissions (`chmod +x`)
- Try setting `APPIMAGE_EXTRACT_AND_RUN=1`

### APT Version Issues
- APT version may be older than latest release
- Check Ubuntu package repository for available versions

### Build Issues
- Ensure internet connectivity for download method
- Check GitHub API rate limits
- Verify AppImage availability in releases

## 📝 Notes

- The `privileged: true` flag is required for AppImage execution
- External AppImages are mounted read-only for security
- All methods support the same MCP server functionality
- The `download.sh` script can be used independently of Docker 
