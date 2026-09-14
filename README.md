# CCRES labelling tools

A ACTRIS-CCRES package containing tools used to label nNational Facilities

## Prerequisites

- [uv](https://docs.astral.sh/uv/) - Python package manager
- Python >= 3.13

## Installation

```bash
# Install project dependencies
uv sync
```

## Usage

```bash
uv run python -m ccres_labelling_tools.core
```

## Development

### Installation

Install the development dependencies and tools:

```bash
# Install just
uv tool install rust-just

# Install all dependency groups
uv sync --all-groups

# Install pre-commit hooks
uv run pre-commit install
```

### Development tasks

Most development tasks are available through the `justfile`.

To list all available commands:

```bash
just
```

### Check the development environment

```bash
just check-install
```

### Create the initial commit

Stage the files to include in the initial commit, then run:

```bash
just initial-commit
```

### Code quality

Pre-commit hooks are configured to run automatically on each commit:

- **ruff check** - Linting with auto-fix
- **ruff format** - Code formatting
- **ty** - Type checking

To run them manually:

```bash
just pre-commit
```

### Running tests

```bash
just test
```

### Building the documentation

```bash
just docs-build
```

To serve the documentation locally:

```bash
just docs-serve
```

### Run all checks

```bash
just all
```

### Bump version and generate changelog

This template uses [commitizen](https://commitizen-tools.github.io/commitizen/) for versioning and changelog generation. Follow the Conventional Commits specification when writing commit messages.

To bump the version and generate a changelog:

```bash
just bump patch
just bump minor
just bump major
```

## Project structure

```
ccres-labelling-tools/
├── src/
│   └── ccres_labelling_tools/
│       ├── __init__.py
│       └── core.py
├── tests/
│   ├── __init__.py
│   └── test_core.py
├── pyproject.toml
└── README.md
```

## License

This project is licensed under the AGPL-3.0 License.
