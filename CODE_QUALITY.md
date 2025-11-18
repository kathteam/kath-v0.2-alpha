# Code Quality Tools

This document describes the code quality tools configured for the KATH project.

## Overview

The project uses automated code formatting, linting, and type checking to maintain consistent code quality:

- **Backend (Python)**: Black, isort, flake8, mypy
- **Frontend (TypeScript/React)**: ESLint, Prettier (already configured)
- **Pre-commit hooks**: Automatic checks before each commit
- **CI/CD**: Automated quality checks on pull requests

## Backend Tools

### Black - Code Formatter

Black automatically formats Python code to a consistent style.

**Configuration**: `app/back_end/pyproject.toml`

```bash
# Format all code
cd app/back_end
black src/ tests/

# Check without modifying
black src/ tests/ --check

# Format specific file
black src/config.py
```

**Settings**:

- Line length: 120 characters
- Target: Python 3.12

### isort - Import Sorter

isort organizes import statements in a consistent order.

```bash
# Sort all imports
cd app/back_end
isort src/ tests/

# Check without modifying
isort src/ tests/ --check-only
```

**Settings**:

- Profile: black (compatible with Black)
- Line length: 120 characters

### flake8 - Linter

flake8 checks code for style issues and potential errors.

**Configuration**: `app/back_end/.flake8`

```bash
# Lint all code
cd app/back_end
flake8 src/ tests/

# Lint specific file
flake8 src/config.py
```

**Settings**:

- Line length: 120 characters
- Max complexity: 10
- Ignores: E203, E266, E501, W503, F403, F401

### mypy - Type Checker

mypy performs static type checking on Python code.

**Configuration**: `app/back_end/pyproject.toml`

```bash
# Type check source code
cd app/back_end
mypy src/

# Type check specific file
mypy src/config.py
```

**Settings**:

- Python version: 3.12
- Check untyped definitions: enabled
- Ignore missing imports: true (for third-party packages)

## Frontend Tools

### ESLint - JavaScript/TypeScript Linter

ESLint identifies problems in JavaScript/TypeScript code.

**Configuration**: `app/front_end/.eslintrc.cjs`

```bash
# Lint frontend code
cd app/front_end
npm run lint

# Auto-fix issues
npm run lint -- --fix
```

### Prettier - Code Formatter

Prettier formats JavaScript/TypeScript/CSS/Markdown files.

**Configuration**: `app/front_end/.prettierrc.cjs`

```bash
# Format frontend code
cd app/front_end
npx prettier --write "src/**/*.{ts,tsx,js,jsx,json,css,md}"

# Check formatting
npx prettier --check "src/**/*.{ts,tsx,js,jsx,json,css,md}"
```

## Pre-commit Hooks

Pre-commit hooks automatically run quality checks before each commit.

### Installation

```bash
# Install pre-commit (already in requirements_dev.txt)
pip install pre-commit

# Install hooks
pre-commit install
```

### Usage

```bash
# Hooks run automatically on git commit
git commit -m "Your message"

# Run hooks manually on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files

# Skip hooks for a single commit (not recommended)
git commit -m "Message" --no-verify
```

### Configured Hooks

1. **General checks**:
   - Trailing whitespace removal
   - End-of-file fixer
   - YAML/JSON/TOML validation
   - Large file detection
   - Private key detection

2. **Python hooks**:
   - Black (formatting)
   - isort (import sorting)
   - flake8 (linting)
   - mypy (type checking)

3. **Frontend hooks**:
   - ESLint (linting with auto-fix)
   - Prettier (formatting)

4. **Documentation hooks**:
   - Markdown linting

## CI/CD Integration

### GitHub Actions Example

Create `.github/workflows/code-quality.yml`:

```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  backend-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          cd app/back_end
          pip install -r requirements.txt requirements_dev.txt
      - name: Run Black
        run: |
          cd app/back_end
          black --check src/ tests/
      - name: Run isort
        run: |
          cd app/back_end
          isort --check-only src/ tests/
      - name: Run flake8
        run: |
          cd app/back_end
          flake8 src/ tests/
      - name: Run mypy
        run: |
          cd app/back_end
          mypy src/

  frontend-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd app/front_end
          npm ci
      - name: Run ESLint
        run: |
          cd app/front_end
          npm run lint
      - name: Run Prettier
        run: |
          cd app/front_end
          npx prettier --check "src/**/*.{ts,tsx,js,jsx,json,css,md}"
```

## Quick Reference

### Before Committing

```bash
# Backend
cd app/back_end
black src/ tests/
isort src/ tests/
flake8 src/ tests/
mypy src/

# Frontend
cd app/front_end
npm run lint -- --fix
npx prettier --write "src/**/*.{ts,tsx,js,jsx,json,css,md}"

# Or use pre-commit for everything
pre-commit run --all-files
```

### Fixing Common Issues

**Import order issues**:

```bash
cd app/back_end
isort src/ tests/
```

**Formatting issues**:

```bash
cd app/back_end
black src/ tests/
```

**Type errors**:

```bash
# Add type hints or use # type: ignore comments
cd app/back_end
mypy src/ --show-error-codes
```

**Linting issues**:

```bash
# Fix automatically where possible
cd app/back_end
autopep8 --in-place --aggressive --aggressive src/
```

## Configuration Files

- **Backend**:
  - `app/back_end/pyproject.toml` - Black, isort, mypy, pytest configuration
  - `app/back_end/.flake8` - flake8 configuration

- **Frontend**:
  - `app/front_end/.eslintrc.cjs` - ESLint configuration
  - `app/front_end/.prettierrc.cjs` - Prettier configuration

- **Pre-commit**:
  - `.pre-commit-config.yaml` - Pre-commit hooks configuration

## VSCode Integration

Add to `.vscode/settings.json`:

```json
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

## Best Practices

1. **Run pre-commit hooks locally** before pushing
2. **Fix issues immediately** - don't accumulate technical debt
3. **Use auto-formatters** - let tools handle style
4. **Add type hints** to new Python code
5. **Keep configuration consistent** across the team
6. **Review tool output** - don't blindly accept changes

## Troubleshooting

**Pre-commit hooks failing**:

```bash
# Update hooks
pre-commit autoupdate

# Clear cache and retry
pre-commit clean
pre-commit run --all-files
```

**Conflicting formatters**:

- Black and isort are configured to work together
- flake8 is configured to ignore Black's style choices
- Run Black first, then isort

**Type checking errors**:

- Add `# type: ignore` for unavoidable errors
- Use `cast()` for complex type situations
- Ignore third-party packages: set `ignore_missing_imports = true`

## Resources

- [Black documentation](https://black.readthedocs.io/)
- [isort documentation](https://pycqa.github.io/isort/)
- [flake8 documentation](https://flake8.pycqa.org/)
- [mypy documentation](https://mypy.readthedocs.io/)
- [pre-commit documentation](https://pre-commit.com/)
- [ESLint documentation](https://eslint.org/)
- [Prettier documentation](https://prettier.io/)
