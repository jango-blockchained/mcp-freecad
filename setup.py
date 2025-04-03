#!/usr/bin/env python3
"""
Setup script for MCP-FreeCAD server
"""

from setuptools import setup, find_packages
import os

# Read requirements from requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

# Read long description from README.md
long_description = ""
if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()

setup(
    name="mcp-freecad",
    version="0.1.0",
    author="MCP-FreeCAD Team",
    author_email="author@example.com",
    description="A Model Context Protocol (MCP) server for FreeCAD",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/user/mcp-freecad",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: CAD",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "mcp-freecad=mcp_freecad.server.freecad_mcp_server:main",
            "freecad-mcp=freecad_mcp:main",
        ],
    },
)
