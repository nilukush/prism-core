# Contributing to PRISM

Thank you for your interest in contributing to PRISM! We welcome contributions from the community and are grateful for any help you can provide.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please read it before contributing.

## How to Contribute

### Reporting Issues

- Check if the issue already exists in our [issue tracker](https://github.com/prism-ai/prism-core/issues)
- If not, create a new issue with a clear title and description
- Include steps to reproduce, expected behavior, and actual behavior
- Add relevant labels and screenshots if applicable

### Suggesting Features

- Open a discussion in [GitHub Discussions](https://github.com/prism-ai/prism-core/discussions)
- Describe the feature and its use case
- Explain how it benefits users
- Wait for community feedback before implementing

### Contributing Code

1. **Fork the Repository**
   ```bash
   git clone https://github.com/YOUR-USERNAME/prism-core.git
   cd prism-core
   ```

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

3. **Set Up Development Environment**
   ```bash
   # Install Poetry
   curl -sSL https://install.python-poetry.org | python3 -
   
   # Install dependencies
   poetry install
   
   # Set up pre-commit hooks
   poetry run pre-commit install
   
   # Copy environment variables
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Make Your Changes**
   - Follow the coding standards below
   - Write tests for new features
   - Update documentation as needed
   - Ensure all tests pass

5. **Test Your Changes**
   ```bash
   # Run tests
   make test
   
   # Run linters
   make lint
   
   # Format code
   make format
   ```

6. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   # or
   git commit -m "fix: resolve bug in X"
   ```
   
   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `style:` Code style changes
   - `refactor:` Code refactoring
   - `test:` Test changes
   - `chore:` Build process or auxiliary tool changes

7. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a PR on GitHub with:
   - Clear title and description
   - Link to related issues
   - Screenshots/demos if applicable

## Development Guidelines

### Code Style

- **Python**: We use Black for formatting and Ruff for linting
  ```bash
  poetry run black backend/
  poetry run ruff check backend/
  ```

- **Type Hints**: Use type hints for all functions
  ```python
  def process_data(input_data: Dict[str, Any]) -> ProcessedResult:
      ...
  ```

- **Docstrings**: Use Google-style docstrings
  ```python
  def function(param1: str, param2: int) -> bool:
      """
      Brief description.
      
      Args:
          param1: Description of param1
          param2: Description of param2
          
      Returns:
          Description of return value
          
      Raises:
          ValueError: When validation fails
      """
  ```

### Testing

- Write tests for all new features
- Maintain test coverage above 80%
- Use pytest for testing
- Mock external dependencies

Example test:
```python
@pytest.mark.asyncio
async def test_create_story(client: AsyncClient):
    """Test story creation."""
    response = await client.post(
        "/api/v1/stories",
        json={"title": "Test Story", "description": "Test"}
    )
    assert response.status_code == 201
```

### Database Migrations

- Use Alembic for migrations
- Test migrations on a copy of production data
- Include both upgrade and downgrade paths

```bash
# Create migration
poetry run alembic revision --autogenerate -m "add new table"

# Run migrations
poetry run alembic upgrade head
```

### API Design

- Follow RESTful principles
- Use consistent naming conventions
- Version APIs appropriately
- Document all endpoints

### Security

- Never commit sensitive data
- Use environment variables for secrets
- Validate all inputs
- Follow OWASP guidelines

## Pull Request Process

1. Ensure all tests pass
2. Update documentation
3. Add changelog entry if significant
4. Request review from maintainers
5. Address review comments
6. Squash commits if requested
7. Merge after approval

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release PR
4. After merge, tag release
5. GitHub Actions will handle deployment

## Getting Help

- Join our [Discord](https://discord.gg/prism-ai)
- Check [Documentation](https://docs.prism-ai.dev)
- Ask in GitHub Discussions
- Email: contributors@prism-ai.dev

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Given credit in documentation

Thank you for contributing to PRISM! 🚀