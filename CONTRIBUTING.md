# Contributing to filelayer

Thank you for considering contributing to filelayer! This guide will help you get started.

## Development Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/sireto/filelayer.git
   cd filelayer
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

3. Install pre-commit hooks:

   ```bash
   pre-commit install
   ```

## Running Tests

```bash
pytest -v
```

## Code Quality

We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting, and [mypy](https://mypy-lang.org/) for type checking.

```bash
ruff check src/ tests/
ruff format src/ tests/
mypy src/
```

Pre-commit hooks run these automatically before each commit.

## Submitting Changes

1. Fork the repository and create a feature branch from `main`.
2. Make your changes with clear, descriptive commit messages.
3. Add or update tests for any new or changed functionality.
4. Ensure all tests pass and linting is clean.
5. Open a pull request against `main`.

## Reporting Issues

- Use [GitHub Issues](https://github.com/sireto/filelayer/issues) to report bugs or request features.
- Include steps to reproduce, expected behavior, and actual behavior.
- Include your Python version and OS.

## Code Style

- All public functions and classes should have docstrings.
- Use type hints on all function signatures.
- Follow existing patterns in the codebase.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
