# Contributing to RishiAI MCP Server

First off, thank you for considering contributing to RishiAI! It's people like you that make this project such a great tool.

## Getting Started

1. Fork the repository on GitHub.
2. Clone your fork locally.
3. Install the development dependencies:
   ```bash
   pip install -e "."
   pip install pytest
   ```

## Development Workflow

1. Create a branch for your feature or bug fix.
2. Make your changes in the codebase.
3. Add or update tests as necessary.
4. Run the test suite to ensure everything is working:
   ```bash
   pytest -q
   ```
5. Ensure your code follows the standard Python coding style.
6. Commit your changes and push them to your fork.
7. Open a Pull Request against the `main` branch of this repository.

## Adding New Tools

If you are adding a new tool to the MCP server:
- Ensure the underlying logic exists in the `dashaflow` library. If it doesn't, please submit a PR to `dashaflow` first.
- Wrap the function in `rishi_ai_mcp.py` using the `@mcp.tool()` decorator.
- Provide a clear docstring detailing the parameters and return values.

## Issues and Feature Requests

If you find a bug or have a feature request, please open an issue on GitHub. Provide as much detail as possible, including steps to reproduce bugs.

Thank you!
