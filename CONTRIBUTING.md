# Contributing to PRISM

🎉 **Welcome to the PRISM Open Source Community!** 🎉

First off, thank you for considering contributing to PRISM! It's people like you that make PRISM such a great tool. We welcome contributions from everyone, regardless of their experience level.

**PRISM is now open source** and we're excited to build this platform together with the community. Whether you're fixing a bug, adding a feature, improving documentation, or sharing ideas - every contribution matters!

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Process](#development-process)
- [Style Guidelines](#style-guidelines)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by the [PRISM Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Git

### Setting Up Your Development Environment

1. **Fork the repository**
   
   Click the "Fork" button in the top right corner of the [PRISM repository](https://github.com/nilukush/prism-core).

2. **Clone your fork**
   
   ```bash
   git clone https://github.com/YOUR_USERNAME/prism-core.git
   cd prism-core
   git remote add upstream https://github.com/nilukush/prism-core.git
   ```

3. **Set up the development environment**
   
   ```bash
   # Copy environment variables
   cp .env.example .env
   
   # Start with Docker Compose
   docker compose up -d
   
   # Or run manually:
   # Backend: cd backend && pip install -r requirements.txt && uvicorn src.main:app --reload
   # Frontend: cd frontend && npm install && npm run dev
   ```

4. **Create a branch**
   
   ```bash
   git checkout -b feature/your-feature-name
   ```

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the [existing issues](https://github.com/prism-ai/prism-core/issues) as you might find out that you don't need to create one.

**How to Submit a Good Bug Report:**

- Use a clear and descriptive title
- Describe the exact steps to reproduce the problem
- Provide specific examples to demonstrate the steps
- Describe the behavior you observed and what behavior you expected
- Include screenshots if applicable
- Include your environment details (OS, Python version, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- A clear and descriptive title
- A detailed description of the proposed enhancement
- Examples of how the enhancement would be used
- Why this enhancement would be useful to most PRISM users

### Your First Code Contribution

Unsure where to begin? You can start by looking through these issues:

- [Good First Issues](https://github.com/prism-ai/prism-core/labels/good%20first%20issue) - issues which should only require a few lines of code
- [Help Wanted](https://github.com/prism-ai/prism-core/labels/help%20wanted) - issues which need extra attention

### Pull Requests

Please follow these steps:

1. Make sure your code follows our [style guidelines](#style-guidelines)
2. Write or update tests for your changes
3. Update documentation if needed
4. Run the test suite: `make test`
5. Run linters: `make lint`
6. Commit your changes following our [commit guidelines](#commit-guidelines)
7. Push to your fork and submit a pull request

## Development Process

### Project Structure

```
prism-core/
├── backend/          # Python backend (FastAPI)
│   ├── src/         # Source code
│   ├── tests/       # Test files
│   └── alembic/     # Database migrations
├── frontend/        # Next.js frontend
│   ├── src/         # Source code
│   └── public/      # Static assets
├── k8s/            # Kubernetes manifests
├── helm/           # Helm charts
├── scripts/        # Development scripts
└── docs/           # Documentation
```

### Running Tests

```bash
# Run all tests
make test

# Run backend tests
cd backend && pytest

# Run frontend tests
cd frontend && npm test

# Run specific test file
pytest backend/tests/test_auth.py

# Run with coverage
pytest --cov=src backend/tests/
```

### Code Quality

```bash
# Run all linters
make lint

# Format Python code
cd backend && black src/ tests/

# Format TypeScript/JavaScript code
cd frontend && npm run format

# Type checking
cd backend && mypy src/
cd frontend && npm run type-check
```

## Style Guidelines

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with the following additions:

- Use type hints for all function signatures
- Maximum line length is 88 characters (Black default)
- Use f-strings for string formatting
- Docstrings should follow Google style

```python
# Good example
from typing import List, Optional

async def create_agent(
    name: str,
    config: dict,
    tools: Optional[List[str]] = None
) -> Agent:
    """Create a new AI agent.
    
    Args:
        name: The name of the agent
        config: Agent configuration dictionary
        tools: Optional list of tool names to enable
        
    Returns:
        The created Agent instance
        
    Raises:
        ValueError: If the configuration is invalid
    """
    # Implementation
```

### TypeScript/JavaScript Style Guide

- Use TypeScript for all new code
- Follow the Airbnb JavaScript Style Guide
- Use functional components with hooks for React
- Prefer named exports over default exports

```typescript
// Good example
export interface AgentConfig {
  name: string
  model: string
  temperature?: number
}

export const createAgent = async (
  config: AgentConfig
): Promise<Agent> => {
  // Implementation
}
```

### CSS/Styling Guidelines

- Use Tailwind CSS utility classes
- Create custom components using CVA (class-variance-authority)
- Follow mobile-first responsive design

## Commit Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that don't affect code meaning
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **perf**: Code change that improves performance
- **test**: Adding or updating tests
- **chore**: Changes to build process or auxiliary tools

### Examples

```bash
# Feature
git commit -m "feat(agents): add memory persistence for chat agents"

# Bug fix
git commit -m "fix(auth): resolve JWT token expiration issue"

# Documentation
git commit -m "docs(api): update workspace endpoints documentation"

# Breaking change
git commit -m "feat(api)!: change agent configuration schema

BREAKING CHANGE: The 'config' field now requires a 'model' property"
```

## Pull Request Process

1. **Before submitting:**
   - Ensure all tests pass
   - Update documentation if needed
   - Add tests for new functionality
   - Run linters and fix any issues

2. **PR Title:**
   Follow the same convention as commit messages

3. **PR Description:**
   Use the PR template and include:
   - Description of changes
   - Related issue numbers
   - Screenshots (for UI changes)
   - Migration instructions (if applicable)

4. **Review Process:**
   - At least one maintainer approval required
   - All CI checks must pass
   - Resolve all review comments

5. **After Approval:**
   - Squash and merge for feature branches
   - Rebase and merge for release branches

## Release Process

1. **Version Bumping:**
   We use semantic versioning (MAJOR.MINOR.PATCH)

2. **Release Notes:**
   - Generated automatically from commit messages
   - Reviewed and edited by maintainers

3. **Release Cycle:**
   - Major releases: Quarterly
   - Minor releases: Monthly
   - Patch releases: As needed

## Documentation

### Where to Add Documentation

- **API Changes**: Update OpenAPI schemas and endpoint documentation
- **New Features**: Add to user guide in `/docs`
- **Configuration**: Update environment variable documentation
- **Architecture**: Update technical documentation

### Documentation Standards

- Use clear, concise language
- Include code examples
- Add diagrams for complex concepts
- Keep documentation up-to-date with code changes

## Community

### Getting Help

- **Discord**: Join our [Discord server](https://prism.io/discord)
- **GitHub Discussions**: Ask questions in [Discussions](https://github.com/prism-ai/prism-core/discussions)
- **Stack Overflow**: Tag questions with `prism-ai`

### Weekly Meetings

We hold community meetings every Thursday at 4 PM UTC. Meeting notes and recordings are available in the [community repository](https://github.com/prism/community).

### Recognition

We believe in recognizing contributors:

- Contributors are added to our [Contributors page](https://prism.io/contributors)
- Significant contributions are highlighted in release notes
- Active contributors may be invited to join the maintainer team

## Development Tips

### Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with debugger
python -m debugpy --listen 5678 --wait-for-client -m uvicorn src.main:app

# Frontend debugging
cd frontend && npm run dev -- --inspect
```

### Performance Testing

```bash
# Run performance tests
cd backend && locust -f tests/performance/locustfile.py

# Profile Python code
python -m cProfile -o profile.stats src/main.py
```

### Database Migrations

```bash
# Create a new migration
cd backend && alembic revision -m "add_new_field_to_agents"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## License

By contributing to PRISM, you agree that your contributions will be licensed under the Apache License 2.0.

---

Thank you for contributing to PRISM! Your efforts help make AI agent development accessible to everyone. 🎉