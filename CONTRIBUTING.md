# Contributing to KATH

Thank you for your interest in contributing to KATH! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in all interactions.

### Expected Behavior

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment or discriminatory language
- Trolling or insulting comments
- Public or private harassment
- Publishing others' private information

---

## Getting Started

### Prerequisites

Before contributing, ensure you have:

1. **Development Environment Setup**
   - Follow [DEVELOPER_SETUP.md](docs/DEVELOPER_SETUP.md)
   - Verify all tests pass: `pytest` (backend) and `npm test` (frontend)

2. **Familiarize Yourself with the Codebase**
   - Read [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)
   - Review [REFACTORING_PLAN.md](REFACTORING_PLAN.md)
   - Explore existing code

3. **Find an Issue to Work On**
   - Check [GitHub Issues](https://github.com/your-repo/kath/issues)
   - Look for issues labeled `good first issue` or `help wanted`
   - Comment on the issue to claim it

---

## Development Workflow

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/kath.git
cd kath

# Add upstream remote
git remote add upstream https://github.com/original-repo/kath.git
```

### 2. Create a Feature Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

**Branch Naming Convention:**
- `feature/description` - New features
- `fix/description` - Bug fixes
- `refactor/description` - Code refactoring
- `docs/description` - Documentation updates
- `test/description` - Test additions/updates

### 3. Make Your Changes

- Write clear, readable code
- Follow coding standards (see below)
- Add tests for new functionality
- Update documentation as needed

### 4. Commit Your Changes

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git add .
git commit -m "type(scope): description"
```

**Commit Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, no logic change)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks
- `perf:` - Performance improvements

**Examples:**
```bash
git commit -m "feat(api): add statistical analysis endpoint"
git commit -m "fix(frontend): resolve data grid pagination issue"
git commit -m "docs(api): update API reference for new endpoints"
git commit -m "test(tools): add unit tests for SpliceAI integration"
```

### 5. Keep Your Branch Updated

```bash
# Fetch latest changes
git fetch upstream

# Rebase your branch
git rebase upstream/main

# Resolve conflicts if any
# Then continue
git rebase --continue
```

### 6. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 7. Create a Pull Request

- Go to GitHub and create a Pull Request
- Fill out the PR template (see below)
- Link related issues
- Request review from maintainers

---

## Coding Standards

### Backend (Python)

**Style Guide:** PEP 8

**Formatting:**
```bash
# Format with Black
black src/

# Sort imports
isort src/

# Check linting
flake8 src/

# Type checking
mypy src/
```

**Code Style:**
```python
# Good
def calculate_revel_score(chromosome: str, position: int, ref: str, alt: str) -> float:
    """
    Calculate REVEL pathogenicity score for a variant.

    Args:
        chromosome: Chromosome name (e.g., 'chr1')
        position: Genomic position
        ref: Reference allele
        alt: Alternate allele

    Returns:
        REVEL score (0-1), or None if not found

    Raises:
        ValueError: If inputs are invalid
    """
    if not chromosome or position < 0:
        raise ValueError("Invalid variant coordinates")

    score = query_revel_database(chromosome, position, ref, alt)
    return score
```

**Key Principles:**
- Use type hints for all function signatures
- Write docstrings for all public functions (Google style)
- Prefer explicit over implicit
- Keep functions small and focused (<50 lines)
- Use descriptive variable names
- Avoid global state

### Frontend (TypeScript/React)

**Style Guide:** Airbnb JavaScript Style Guide

**Formatting:**
```bash
# Format with Prettier
npm run format

# Check linting
npm run lint
```

**Code Style:**
```typescript
// Good
interface VariantRowProps {
  variant: Variant;
  onEdit: (variant: Variant) => void;
  selected?: boolean;
}

const VariantRow: React.FC<VariantRowProps> = ({ variant, onEdit, selected = false }) => {
  const handleClick = useCallback(() => {
    onEdit(variant);
  }, [variant, onEdit]);

  return (
    <TableRow selected={selected} onClick={handleClick}>
      <TableCell>{variant.chromosome}</TableCell>
      <TableCell>{variant.position}</TableCell>
    </TableRow>
  );
};

export default React.memo(VariantRow);
```

**Key Principles:**
- Use functional components with hooks
- Prefer composition over inheritance
- Use TypeScript strict mode
- Memoize expensive computations (useMemo, useCallback)
- Keep components small (<300 lines)
- Extract reusable logic into custom hooks

### File Naming

**Backend:**
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions: `snake_case()`
- Constants: `UPPER_SNAKE_CASE`

**Frontend:**
- Components: `PascalCase.tsx`
- Utilities: `camelCase.ts`
- Hooks: `use<Name>.ts`
- Types: `PascalCase.ts` (in `types/` directory)

---

## Testing Guidelines

### Backend Tests

**Framework:** pytest

**Running Tests:**
```bash
cd app/back_end
pytest
pytest --cov=src --cov-report=html  # With coverage
pytest tests/test_specific.py -v     # Specific test file
```

**Writing Tests:**
```python
import pytest
from src.tools.revel import get_single_revel_score

def test_revel_score_found():
    """Test REVEL score retrieval for known variant"""
    score = get_single_revel_score('chr1', 12345, 'A', 'T')
    assert score is not None
    assert 0 <= score <= 1

def test_revel_score_not_found():
    """Test REVEL score for non-existent variant"""
    score = get_single_revel_score('chr99', 99999999, 'X', 'Y')
    assert score is None

def test_revel_score_invalid_input():
    """Test REVEL with invalid input"""
    with pytest.raises(ValueError):
        get_single_revel_score('', -1, 'A', 'T')
```

**Test Coverage Requirements:**
- New code: >80% coverage
- Critical paths: 100% coverage
- Run coverage report before submitting PR

### Frontend Tests

**Framework:** Vitest + React Testing Library

**Running Tests:**
```bash
cd app/front_end
npm test
npm run test:coverage
```

**Writing Tests:**
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { VariantRow } from './VariantRow';

describe('VariantRow', () => {
  const mockVariant = {
    id: '1',
    chromosome: 'chr1',
    position: 12345,
  };

  it('renders variant data correctly', () => {
    render(<VariantRow variant={mockVariant} onEdit={jest.fn()} />);

    expect(screen.getByText('chr1')).toBeInTheDocument();
    expect(screen.getByText('12345')).toBeInTheDocument();
  });

  it('calls onEdit when clicked', () => {
    const handleEdit = jest.fn();
    render(<VariantRow variant={mockVariant} onEdit={handleEdit} />);

    fireEvent.click(screen.getByRole('row'));
    expect(handleEdit).toHaveBeenCalledWith(mockVariant);
  });
});
```

---

## Pull Request Process

### Before Submitting

**Checklist:**
- [ ] Code follows style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] Branch rebased on latest main
- [ ] No merge conflicts

### PR Template

```markdown
## Description
<!-- Describe your changes in detail -->

## Related Issue
<!-- Link to the issue this PR addresses -->
Closes #123

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Changes Made
<!-- List specific changes -->
- Added statistical analysis API endpoint
- Updated frontend to display charts
- Added tests for new functionality

## How Has This Been Tested?
<!-- Describe testing performed -->
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

## Screenshots (if applicable)
<!-- Add screenshots for UI changes -->

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
```

### Review Process

1. **Automated Checks**
   - CI/CD runs tests
   - Code quality checks
   - Coverage report

2. **Code Review**
   - At least one maintainer must approve
   - Address all feedback
   - Make requested changes

3. **Merge**
   - Squash and merge (default)
   - Rebase and merge (for multi-commit PRs)
   - Merge commit (rarely used)

### After Merge

- Delete your feature branch
- Update your local repository
- Celebrate! 

---

## Issue Reporting

### Bug Reports

**Use the bug report template:**

```markdown
**Describe the Bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment**
- OS: [e.g., macOS 13.0, Windows 11, Ubuntu 22.04]
- Browser: [e.g., Chrome 120, Firefox 119]
- KATH Version: [e.g., 0.2-alpha]

**Additional Context**
Add any other context about the problem here.
```

### Feature Requests

**Use the feature request template:**

```markdown
**Is your feature request related to a problem?**
A clear and concise description of what the problem is.

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

**Additional context**
Add any other context or screenshots about the feature request here.
```

---

## Communication

### Where to Ask Questions

- **General Questions:** GitHub Discussions
- **Bug Reports:** GitHub Issues
- **Feature Requests:** GitHub Issues
- **Security Issues:** Email maintainers privately

### Response Times

- Issues: We aim to respond within 3 business days
- Pull Requests: We aim to review within 5 business days
- Critical bugs: We aim to respond within 24 hours

---

## Recognition

Contributors will be recognized in:
- README.md Contributors section
- Release notes
- GitHub contributors page

Thank you for contributing to KATH! 

---

## Additional Resources

- [Developer Setup Guide](docs/DEVELOPER_SETUP.md)
- [Architecture Documentation](docs/architecture/ARCHITECTURE.md)
- [API Reference](docs/api/API_REFERENCE.md)
- [Refactoring Plan](REFACTORING_PLAN.md)

---

**Last Updated:** 2025-10-27
