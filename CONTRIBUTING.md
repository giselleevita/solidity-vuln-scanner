# Contributing to Solidity Vuln Scanner

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/solidity-vuln-scanner.git
   cd solidity-vuln-scanner
   ```
3. **Set up development environment**:
   ```bash
   make install
   # or manually:
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write clean, documented code
   - Follow existing code style
   - Add tests for new features
   - Update documentation as needed

3. **Run tests**:
   ```bash
   make test
   # or
   pytest -v
   ```

4. **Test locally**:
   ```bash
   # Terminal 1: Start API
   make api
   
   # Terminal 2: Start UI
   make ui
   ```

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

6. **Push and create Pull Request**:
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a PR on GitHub.

## Code Style

- Follow PEP 8 Python style guide
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and small

## Testing

- Add tests for new vulnerability detection patterns
- Test edge cases and error handling
- Ensure existing tests still pass
- Aim for good test coverage

## Adding New Vulnerability Patterns

To add a new vulnerability detection pattern:

1. Edit `static_analyzer.py`
2. Add pattern to `_init_patterns()` method
3. Add description to `VULN_TYPES` in `app_config.py`
4. Add test case in `tests/test_static_analyzer.py`
5. Update documentation

## Reporting Issues

When reporting bugs or suggesting features:

- Use clear, descriptive titles
- Provide steps to reproduce (for bugs)
- Include relevant code examples
- Mention your Python version and OS

## Questions?

Feel free to open an issue for questions or discussions!

