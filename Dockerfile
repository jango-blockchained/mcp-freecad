FROM ubuntu:22.04

# Build argument to control FreeCad installation method
# Options: download, external, apt
ARG FREECAD_INSTALL_METHOD=download

WORKDIR /app

# Install base packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    curl \
    wget \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-pip \
    python3.11-venv \
    procps \
    libgl1-mesa-glx \
    libx11-6 \
    libxcb1 \
    libxext6 \
    xvfb \
    libpulse0

# Install FreeCad via apt if method is 'apt'
RUN if [ "$FREECAD_INSTALL_METHOD" = "apt" ]; then \
        apt-get install -y --no-install-recommends freecad freecad-python3; \
    fi

# Install AppImage dependencies if method is 'download' or 'external'
RUN if [ "$FREECAD_INSTALL_METHOD" = "download" ] || [ "$FREECAD_INSTALL_METHOD" = "external" ]; then \
        apt-get install -y --no-install-recommends \
        fuse \
        libfuse2 \
        libglib2.0-0 \
        libgtk-3-0 \
        libxss1 \
        libgconf-2-4 \
        libxrandr2 \
        libasound2 \
        libpangocairo-1.0-0 \
        libatk1.0-0 \
        libcairo-gobject2 \
        libgtk-3-0 \
        libgdk-pixbuf2.0-0 \
        libxcomposite1 \
        libxcursor1 \
        libxdamage1 \
        libxi6 \
        libxtst6 \
        libnss3 \
        libcups2 \
        libxrandr2 \
        libdrm2 \
        libgtk-3-0; \
    fi

# Clean up apt cache
RUN rm -rf /var/lib/apt/lists/*

# Create symbolic links for python3.11
RUN ln -s /usr/bin/python3.11 /usr/bin/python3 \
    && ln -s /usr/bin/python3.11 /usr/bin/python \
    && ln -s /usr/bin/pip3 /usr/bin/pip

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the download script and download AppImage if method is 'download'
COPY download.sh .
RUN chmod +x download.sh
RUN if [ "$FREECAD_INSTALL_METHOD" = "download" ]; then \
        ./download.sh; \
    fi

# Copy the rest of the application
COPY . .

# Set Python path and FreeCad environment variables
ENV PYTHONPATH=/app
ENV QT_QPA_PLATFORM=offscreen
ENV FREECAD_CONSOLE=1
ENV DISPLAY=:99
ENV FREECAD_INSTALL_METHOD=${FREECAD_INSTALL_METHOD}

# Set AppImage-specific environment variables
ENV FREECAD_APPIMAGE_PATH=/app
ENV APPIMAGE_EXTRACT_AND_RUN=1

# Expose the port the app runs on
EXPOSE 8080 12345

# Create symlink for the MCP server script
RUN ln -sf /app/src/mcp_freecad/server/freecad_mcp_server.py /app/freecad_mcp_server.py

# Find and set executable permissions for FreeCad AppImage (if downloaded)
RUN if [ "$FREECAD_INSTALL_METHOD" = "download" ]; then \
        find /app -name "FreeCAD*.AppImage" -exec chmod +x {} \; || true; \
    fi

# Command to run the application
CMD ["python", "manage_servers.py", "start", "all"]
