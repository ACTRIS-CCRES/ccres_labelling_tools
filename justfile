# Run `just` to see available commands

# Display available commands
default:
    @just --list

# Verify that the development environment is correctly configured
check-install:
    @echo "Verifying Python interpreter..."
    @uv run python --version >/dev/null

    @echo "Verifying ccres_labelling_tools..."
    @uv run python -c "import ccres_labelling_tools" >/dev/null

    @echo "Verifying pytest..."
    @uv run pytest --version >/dev/null

    @echo "Verifying ruff..."
    @uv run ruff --version >/dev/null

    @echo "Verifying ty..."
    @uv run ty --version >/dev/null

    @echo "Verifying pre-commit..."
    @uv run pre-commit --version >/dev/null

    @echo "Verifying zensical..."
    @uv run zensical --version >/dev/null

    @echo ""
    @echo "✅ Development environment is correctly configured."

# Create the initial commit (allowed on the default branch)
initial-commit:
    @echo ""
    @echo "Creating initial commit..."
    @SKIP=no-commit-to-branch git commit -m "chore(init): initial commit"

# Run all pre-commit hooks
pre-commit:
    @echo ""
    @echo "Running pre-commit hooks..."
    @uv run pre-commit run --all-files

# Run Python tests
test:
    @echo ""
    @echo "Running Python tests..."
    @uv run pytest

# Generate and build the documentation
docs-build:
    @echo ""
    @echo "Building documentation..."
    @rm -rf public
    @uv run zensical build >/dev/null

# Build and serve the documentation locally
docs-serve: docs-build
    @uv run zensical serve

# Run all project checks
all: pre-commit test docs-build
    @echo ""
    @echo "===================================================================="
    @echo "✅ All checks passed."
    @echo "===================================================================="

# Bump version (major, minor or patch)
bump increment:
    @echo ""
    @echo "Bumping {{increment}} version..."
    @SKIP=no-commit-to-branch uv run cz bump --increment {{ if increment == "major" { "MAJOR" } else if increment == "minor" { "MINOR" } else if increment == "patch" { "PATCH" } else { error("increment must be 'major', 'minor' or 'patch'") } }} --changelog
