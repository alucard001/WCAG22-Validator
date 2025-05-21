# Contributing to WCAG 2.2 Validator

Thank you for your interest in contributing to the WCAG 2.2 Validator! This document provides guidelines and instructions for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Set up a development environment:
   ```bash
   # Create a virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install development dependencies
   pip install -e ".[dev]"
   ```

## Adding a New Criterion

The most valuable contribution is adding support for additional WCAG 2.2 criteria. Here's how to do it:

1. Create a new file in `wcag22_validator/criteria/` named `criterion_X_Y_Z.py` where X, Y, and Z correspond to the WCAG criterion number (e.g., `criterion_1_3_5.py` for criterion 1.3.5).

2. Implement a class that inherits from `BaseCriterion` and overrides the `validate` method:

```python
from .base import BaseCriterion
from ..reporter import ValidationIssue

class Criterion_X_Y_Z(BaseCriterion):
    def __init__(self):
        super().__init__()
        self.id = "X.Y.Z"  # e.g., "1.3.5"
        self.name = "Criterion Name"  # e.g., "Identify Input Purpose"
        self.level = "A"  # or "AA" or "AAA"
        self.url = "https://www.w3.org/WAI/WCAG22/Understanding/criterion-name.html"
        self.description = """
        Description of the criterion as specified in WCAG 2.2.
        """
        
    def validate(self, soup, html_content):
        issues = []
        
        # Implement validation logic here
        # Use self.create_issue() to create issues
        
        return issues
```

3. Make your validation as accurate and comprehensive as possible, but remember that static analysis has limitations.

4. Include helpful error messages and code suggestions in the issues you create.

## Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write clear docstrings in Google or NumPy format
- Use descriptive variable and function names

## Testing

- Add tests for your new criterion in the `tests/` directory
- Make sure all tests pass before submitting a pull request
- Run tests with: `pytest`

## Documentation

When adding a new criterion, make sure to:

1. Document all public methods and classes
2. Add the new criterion to the README.md list of supported criteria
3. Include references to relevant WCAG documentation

## Pull Request Process

1. Create a branch with a descriptive name (`add-criterion-1-3-5`)
2. Make your changes and commit with clear, descriptive commit messages
3. Push to your fork and submit a pull request
4. In the PR description, explain the changes and include references to any related issues

## Code of Conduct

Please follow our code of conduct in all your interactions with the project.

Thank you for helping improve web accessibility!