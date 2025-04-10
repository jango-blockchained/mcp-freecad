#!/usr/bin/env python3
"""
Downloads the latest stable FreeCAD AppImage for Linux x86_64 from GitHub Releases.
"""

import argparse
import requests
import os
import sys
import stat

# --- Configuration ---
GITHUB_REPO = "FreeCAD/FreeCAD"
# Using 'latest' tag which usually points to the most recent stable release
RELEASE_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
# Fallback/alternative: list releases if 'latest' doesn't work as expected
# RELEASE_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
APPIMAGE_FILENAME_CONTAINS = "conda-Linux-x86_64-py311.AppImage" # Updated for FreeCAD 1.0 pattern
# ---------------------

def download_file(url, destination_path, show_progress=True):
    """Downloads a file from a URL, optionally showing progress."""
    try:
        print(f"Downloading from: {url}")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 1024 # 1MB
        progress_bar_length = 40
        start_time = os.path.getctime(destination_path) if os.path.exists(destination_path) else 0

        with open(destination_path, 'wb') as f:
            downloaded = 0
            for data in response.iter_content(block_size):
                f.write(data)
                downloaded += len(data)
                if show_progress and total_size > 0:
                    # Calculate progress
                    percent = int(100 * downloaded / total_size)
                    filled_length = int(progress_bar_length * downloaded // total_size)
                    bar = '█' * filled_length + '-' * (progress_bar_length - filled_length)
                    # Display progress bar
                    sys.stdout.write(f'\rProgress: |{bar}| {percent}% Complete ({downloaded/1024/1024:.1f}/{total_size/1024/1024:.1f} MB)')
                    sys.stdout.flush()
            if show_progress:
                 sys.stdout.write('\n') # New line after completion

        print(f"Successfully downloaded to: {destination_path}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"\nError downloading file: {e}", file=sys.stderr)
        # Clean up potentially incomplete file
        if os.path.exists(destination_path) and os.path.getctime(destination_path) > start_time:
             os.remove(destination_path)
             print(f"Removed incomplete file: {destination_path}")
        return False
    except Exception as e:
        print(f"\nAn unexpected error occurred during download: {e}", file=sys.stderr)
        # Clean up potentially incomplete file
        if os.path.exists(destination_path) and os.path.getctime(destination_path) > start_time:
             os.remove(destination_path)
             print(f"Removed incomplete file: {destination_path}")
        return False


def make_executable(filepath):
    """Makes a file executable."""
    try:
        st = os.stat(filepath)
        os.chmod(filepath, st.st_mode | stat.S_IEXEC)
        print(f"Made {filepath} executable.")
        return True
    except Exception as e:
        print(f"Error making file executable: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Download the latest stable FreeCAD AppImage.")
    parser.add_argument(
        "--output-dir", "-o",
        default=".",
        help="Directory to save the downloaded AppImage (default: current directory)."
    )
    parser.add_argument(
        "--filename", "-f",
        default=None,
        help="Filename for the downloaded AppImage (default: derived from download URL)."
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable the download progress bar."
    )
    args = parser.parse_args()

    print(f"Fetching latest release information from {GITHUB_REPO}...")

    try:
        response = requests.get(RELEASE_API_URL, timeout=15)
        response.raise_for_status()
        release_data = response.json()

        if not isinstance(release_data, dict):
             print(f"Error: Unexpected API response format. Expected a dictionary, got {type(release_data)}", file=sys.stderr)
             sys.exit(1)

        assets = release_data.get("assets", [])
        if not assets:
            print("Error: No assets found in the latest release.", file=sys.stderr)
            sys.exit(1)

        # Find the AppImage asset
        appimage_asset = None
        for asset in assets:
            if APPIMAGE_FILENAME_CONTAINS in asset.get("name", ""):
                appimage_asset = asset
                break

        if not appimage_asset:
            print(f"Error: Could not find an asset matching '{APPIMAGE_FILENAME_CONTAINS}' in the latest release.", file=sys.stderr)
            print("Available assets:")
            for asset in assets:
                print(f"- {asset.get('name')}")
            sys.exit(1)

        download_url = appimage_asset.get("browser_download_url")
        original_filename = appimage_asset.get("name")
        print(f"Found AppImage: {original_filename}")

        if not download_url:
            print("Error: Could not get download URL for the AppImage asset.", file=sys.stderr)
            sys.exit(1)

        # Determine output path
        output_filename = args.filename if args.filename else original_filename
        if not output_filename: # Fallback if name missing from asset and args
             print("Error: Could not determine output filename.", file=sys.stderr)
             sys.exit(1)

        output_path = os.path.join(args.output_dir, output_filename)

        # Create output directory if it doesn't exist
        os.makedirs(args.output_dir, exist_ok=True)

        # Download the file
        if download_file(download_url, output_path, show_progress=not args.no_progress):
            # Make it executable
            make_executable(output_path)
            print("Download and setup complete.")
        else:
            print("Download failed.", file=sys.stderr)
            sys.exit(1)


    except requests.exceptions.RequestException as e:
        print(f"Error fetching release info from GitHub: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
