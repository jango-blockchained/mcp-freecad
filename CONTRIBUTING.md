# Contributing to MCP-FreeCAD

Thank you for your interest in contributing to the MCP-FreeCAD project! This document provides guidelines and information for contributing.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/yourusername/mcp-freecad.git
   cd mcp-freecad
   ```
3. Set up the development environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Development Workflow

1. Create a branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Run tests to ensure everything works:
   ```bash
   # Run the test script
   python test_api.py
   ```
4. Push your changes:
   ```bash
   git push origin feature/your-feature-name
   ```
5. Create a Pull Request on GitHub

## Coding Style

This project follows these coding standards:

- Use Black for code formatting (line length: 88)
- Follow PEP 8 guidelines
- Use type hints for function parameters and return values
- Write docstrings for all functions, classes, and modules

## Project Structure

- `src/mcp_freecad/`: Core implementation modules
  - `api/`: API endpoint implementations
  - `core/`: Core server components
  - `events/`: Event handling system
  - `extractor/`: CAD context extraction
  - `resources/`: Resource providers
  - `tools/`: Tool providers
- `app.py`: Main application entry point
- `test_api.py`: API testing script

## Pull Request Process

1. Update the README.md or documentation with details of changes if appropriate
2. Update the tests to cover your changes
3. Make sure all tests pass
4. The PR will be merged once it is reviewed and approved

## Communication

If you have questions or need help, please:
- Open an issue on GitHub
- Reach out to the maintainers

Thank you for your contributions! 