FROM python:3.12-slim

WORKDIR /app

# Install needed packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install psutil

# Copy the rest of the application
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# Expose the port the app runs on
EXPOSE 8080 12345

# Create symlink for the MCP server script
RUN ln -sf /app/src/mcp_freecad/server/freecad_mcp_server.py /app/freecad_mcp_server.py

# Command to run the application
CMD ["python", "manage_servers.py", "start", "all"]
