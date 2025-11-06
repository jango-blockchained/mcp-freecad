# Contributing to MCP-FreeCAD

Thank you for your interest in contributing to the MCP-FreeCAD project! This document provides guidelines and instructions for contributing to my project.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md). We expect all contributors to abide by these guidelines to ensure a positive and respectful community.

## Development Environment Setup

1. **Fork and Clone the Repository**
   ```bash
   git clone https://github.com/your-username/mcp-freecad.git
   cd mcp-freecad
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -e .
   pip install -r requirements-dev.txt
   ```

## Development Workflow

1. **Create a Branch**
   ```bash
   git checkout -b feature-name
   ```

2. **Make Your Changes**
   - Follow the code style guidelines
   - Write clean, readable code
   - Add comments where necessary

3. **Add Tests**
   - Write tests for new features
   - Ensure existing tests pass

4. **Run Tests**
   ```bash
   pytest tests/ -v
   ```

5. **Check Code Style**
   ```bash
   black --check src tests
   isort --check-only --profile black src tests
   flake8 src tests
   ```

## Pull Request Process

1. **Update Documentation**
   - Update the README.md if necessary
   - Add documentation for new features
   - Update documentation for modified features

2. **Commit Your Changes**
   ```bash
   git commit -m "Add feature X"
   ```

3. **Push to Your Fork**
   ```bash
   git push origin feature-name
   ```

4. **Create a Pull Request**
   - Go to the original repository on GitHub
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill in the PR template

5. **Code Review**
   - Address any comments or feedback
   - Make requested changes
   - Push changes to your branch

## Style Guidelines

### Python Code Style

- Follow PEP 8 guidelines
- Use 4 spaces for indentation (no tabs)
- Use Black for code formatting (line length: 88)
- Use isort for import sorting (profile: black)
- Use meaningful variable and function names
- Keep functions small and focused on a single task
- Add type hints where appropriate
- Write docstrings for public functions and classes

### Commit Messages

- Use the imperative mood ("Add feature" not "Added feature")
- Keep the first line under 50 characters
- Separate subject from body with a blank line
- Use the body to explain what and why, not how

## License

By contributing to MCP-FreeCAD, you agree that your contributions will be licensed under the project's MIT License.

## Questions?

If you have any questions or need help, feel free to open an issue or contact the maintainers directly.

Thank you for contributing to MCP-FreeCAD!

---

<div align="center">
<sub>
With love from jango-blockchained ❤️<br>
Building the future of AI-powered CAD
</sub>
</div> 
