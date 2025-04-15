#!/bin/bash

# Improved script to rename files and update references in project files
# Usage: ./rename_files.sh

set -e  # Exit on error

PROJECT_ROOT="$(pwd)"
echo "Using project root: $PROJECT_ROOT"

# Ask user to clean up any existing .bak files first
echo "It's recommended to delete all .bak files before running this script."
read -p "Delete all .bak files in the project? (y/n): " delete_bak

if [[ "$delete_bak" == "y" || "$delete_bak" == "Y" ]]; then
    echo "Deleting all .bak files..."
    find "$PROJECT_ROOT" -name "*.bak" -delete
    echo "Deleted all .bak files."
fi

# Create a temporary file to track changes
CHANGES_FILE=$(mktemp)

# Define renaming mappings (old_path:new_path)
declare -a RENAME_MAPPINGS=(
    "freecad_socket_server.py:freecad_socket_server.py"
    "freecad_connection_bridge.py:freecad_connection_bridge.py"
    "freecad_connection_wrapper.py:freecad_connection_wrapper.py"
    "freecad_connection_launcher.py:freecad_connection_launcher.py"
    "src/mcp_freecad/client/freecad_connection_manager.py:src/mcp_freecad/client/freecad_connection_manager.py"
    "freecad_launcher_script.py:freecad_launcher_script.py"
)

# Function to update references in files
update_references() {
    local old_name=$1
    local new_name=$2
    local old_basename=$(basename "$old_name")
    local new_basename=$(basename "$new_name")
    local old_module=${old_basename%.py}
    local new_module=${new_basename%.py}

    echo "Updating references from $old_basename to $new_basename..."

    # Find files that might contain references to the old filename
    # Explicitly exclude problematic file types and directories
    find "$PROJECT_ROOT" -type f \
        -not -path "*/\.*" \
        -not -path "*/venv/*" \
        -not -path "*/\node_modules/*" \
        -not -path "*/logs/*" \
        -not -path "*/__pycache__/*" \
        -not -path "*/\squashfs-root/*" \
        -not -name "*.pyc" \
        -not -name "*.so" \
        -not -name "*.o" \
        -not -name "*.a" \
        -not -name "*.png" \
        -not -name "*.jpg" \
        -not -name "*.gif" \
        -not -name "*.bak" \
        -not -name "*.log" \
        -not -name "*.AppImage" \
        -not -name "*.exe" \
        -not -name "*.bin" \
        -not -name "*.dat" \
        | grep -E "\.(py|md|txt|json|html|js|css|sh)$" \
        | xargs grep -l -E "(from[[:space:]]+${old_module}[[:space:]]+import|import[[:space:]]+${old_module}([[:space:]]|$)|[^a-zA-Z0-9_]${old_module}[^a-zA-Z0-9_]|${old_basename})" 2>/dev/null \
        | while read -r file; do

        # Skip the changes file and current script
        if [[ "$file" == "$CHANGES_FILE" ]] || [[ "$file" == "$0" ]]; then
            continue
        fi

        echo "  Updating references in $file"

        # Make backup of the file
        cp "$file" "${file}.bak"

        # Handle specific import patterns with word boundaries to avoid partial matches
        # For specific module imports like "from freecad_connection_manager import FreeCADConnection"
        sed -i "s/from[[:space:]]\+${old_module}[[:space:]]\+import/from ${new_module} import/g" "$file"

        # For direct imports like "import freecad_connection"
        sed -i "s/import[[:space:]]\+${old_module}\([[:space:]]\|$\)/import ${new_module}\1/g" "$file"

        # For "import freecad_connection_manager as fc" type imports
        sed -i "s/import[[:space:]]\+${old_module}[[:space:]]\+as/import ${new_module} as/g" "$file"

        # For relative imports like "from .freecad_connection_manager import"
        sed -i "s/from[[:space:]]\+\.${old_module}[[:space:]]\+import/from .${new_module} import/g" "$file"

        # For relative imports like "from . import freecad_connection_manager"
        sed -i "s/from[[:space:]]\+\.[[:space:]]\+import[[:space:]]\+${old_module}/from . import ${new_module}/g" "$file"

        # For "import mcp_freecad.client.freecad_connection" full path imports
        if [[ "$old_name" == *"/"* ]]; then
            old_import_path=$(echo "$old_name" | sed 's/\.py$//' | sed 's/src\///' | sed 's/\//./g')
            new_import_path=$(echo "$new_name" | sed 's/\.py$//' | sed 's/src\///' | sed 's/\//./g')
            sed -i "s/import[[:space:]]\+${old_import_path}\([[:space:]]\|$\)/import ${new_import_path}\1/g" "$file"
            sed -i "s/from[[:space:]]\+${old_import_path}[[:space:]]\+import/from ${new_import_path} import/g" "$file"
        fi

        # Replace direct file name references with word boundaries to avoid partial matches
        # Use word boundary pattern \b for more accurate matches
        sed -i "s/\b${old_basename}\b/${new_basename}/g" "$file"

        # Handle specific docstring references that may not have word boundaries
        sed -i "s|${old_basename}|${new_basename}|g" "$file"

        # Store changes
        echo "Updated references in $file" >> "$CHANGES_FILE"
    done
}

# Process each mapping
for mapping in "${RENAME_MAPPINGS[@]}"; do
    old_path="${mapping%%:*}"
    new_path="${mapping##*:}"

    # Ensure the old file exists
    if [[ ! -f "$old_path" ]]; then
        echo "Warning: $old_path not found, searching for it in the project..."

        # Try to find the file recursively
        found_path=$(find "$PROJECT_ROOT" -name "$(basename "$old_path")" -type f | head -n 1)

        if [[ -n "$found_path" ]]; then
            echo "Found at: $found_path"
            old_path="$found_path"
            # Update new path to preserve directory structure
            new_dir=$(dirname "$found_path")
            new_path="$new_dir/$(basename "$new_path")"
        else
            echo "Error: Could not find $old_path anywhere in the project. Skipping."
            continue
        fi
    fi

    echo "Renaming $old_path to $new_path"

    # Create target directory if it doesn't exist
    mkdir -p "$(dirname "$new_path")"

    # Update references before renaming the file
    update_references "$old_path" "$new_path"

    # Rename the file
    mv "$old_path" "$new_path"
    echo "Renamed $old_path to $new_path" >> "$CHANGES_FILE"
done

# Additional search for any missed references
echo "Performing final check for missed references..."
for mapping in "${RENAME_MAPPINGS[@]}"; do
    old_path="${mapping%%:*}"
    old_basename=$(basename "$old_path")
    old_module=${old_basename%.py}

    # Check for any remaining references to the old file
    grep -r --include="*.py" --exclude="*.bak" -l "\b${old_module}\b" "$PROJECT_ROOT" 2>/dev/null | while read -r file; do
        echo "WARNING: Possible missed reference to $old_module in $file"
    done
done

# Display summary
echo "-----------------------------------------"
echo "Summary of changes:"
cat "$CHANGES_FILE"
echo "-----------------------------------------"
echo "Backup files with .bak extension have been created for modified files."
echo "If everything looks good, you can remove them with: find $PROJECT_ROOT -name '*.bak' -delete"

# Cleanup
rm "$CHANGES_FILE"

echo "Renaming complete! Please test your application carefully."