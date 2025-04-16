from setuptools import setup, find_packages

setup(
    name="MCPIndicator",
    version="0.2.0",
    description="FreeCAD workbench that shows MCP connection status",
    author="MCP-FreeCAD Team",
    author_email="example@example.com",
    url="https://github.com/yourusername/MCPIndicator",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "PySide2",
        "mcp-freecad>=1.0.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Scientific/Engineering :: Visualization",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
