# PRISM Core - Open Source AI-Powered Product Management Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Overview

PRISM (Product Requirements Intelligence & Strategy Manager) is an enterprise-grade, open-source AI-powered product management platform designed to revolutionize how teams build products. It automates 70% of routine PM tasks while providing strategic insights, resulting in 80% reduction in documentation time and 30-40% faster time-to-market.

## Features

- 🤖 **AI-Powered Agents**: Specialized agents for story generation, document creation, prioritization, and market analysis
- 📝 **Smart User Stories**: Generate well-structured agile stories with acceptance criteria
- 📄 **Automated Documentation**: Create PRDs, technical specs, and other documents
- 🔄 **Enterprise Integrations**: Native support for Jira, Confluence, Slack, and more
- 🏢 **Multi-Tenancy**: Organization-based isolation with role-based access control
- 📊 **Analytics & Insights**: Data-driven decision making with built-in analytics
- 🔒 **Enterprise Security**: JWT auth, encryption, and comprehensive audit logging
- 📈 **Scalable Architecture**: Microservices-ready with Kubernetes support

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/prism-ai/prism-core.git
cd prism-core
```

2. **Set up environment**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# Required: DATABASE_URL, REDIS_URL, and at least one LLM API key
```

3. **Install dependencies**
```bash
# Using Poetry (recommended)
poetry install

# Or using pip
pip install -r requirements.txt
```

4. **Initialize database**
```bash
# Run migrations
poetry run alembic upgrade head

# Create initial data (optional)
poetry run python -m backend.scripts.init_db
```

5. **Start the application**
```bash
# Development mode
poetry run uvicorn backend.src.main:app --reload

# Production mode
poetry run gunicorn backend.src.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

The application will be available at `http://localhost:8000`

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Architecture

PRISM follows a modular, microservices-ready architecture:

```
prism-core/
├── backend/                 # Python backend
│   ├── src/
│   │   ├── agents/         # AI agents
│   │   ├── api/            # REST API endpoints
│   │   ├── core/           # Core functionality
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── middleware/     # Custom middleware
│   ├── tests/              # Test suite
│   └── migrations/         # Database migrations
├── frontend/               # React frontend (TBD)
├── infrastructure/         # Deployment configs
│   ├── docker/            # Docker configurations
│   ├── kubernetes/        # K8s manifests
│   └── terraform/         # Infrastructure as code
└── docs/                  # Documentation
```

## Configuration

### LLM Providers

PRISM supports multiple LLM providers:

```python
# OpenAI
OPENAI_API_KEY=your-key
DEFAULT_LLM_MODEL=gpt-3.5-turbo

# Anthropic
ANTHROPIC_API_KEY=your-key
DEFAULT_LLM_MODEL=claude-3-opus-20240229

# Local (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_LLM_MODEL=llama2
```

### Database

Configure PostgreSQL connection:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/prism_db
```

### Redis Cache

Configure Redis for caching and background tasks:

```bash
REDIS_URL=redis://localhost:6379/0
```

## API Documentation

Once running, access the interactive API documentation:

- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

### Example: Generate User Story

```bash
curl -X POST "http://localhost:8000/api/v1/ai/stories/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "Users should be able to filter products by category",
    "context": "E-commerce platform",
    "priority": "high"
  }'
```

## Development

### Code Style

We use Black for Python code formatting and Ruff for linting:

```bash
# Format code
poetry run black backend/

# Run linter
poetry run ruff check backend/

# Type checking
poetry run mypy backend/
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=backend/src --cov-report=html

# Run specific test
poetry run pytest backend/tests/test_agents.py::test_story_generation
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run manually
poetry run pre-commit run --all-files
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📚 [Documentation](https://docs.prism-ai.dev)
- 💬 [Discord Community](https://discord.gg/prism-ai)
- 🐛 [Issue Tracker](https://github.com/prism-ai/prism-core/issues)
- 📧 [Email Support](mailto:support@prism-ai.dev)

## Acknowledgments

Built with ❤️ by the PRISM community. Special thanks to all our contributors and the open-source projects that make PRISM possible.

---

<div align="center">
  <strong>Ready to transform your product management?</strong><br>
  <a href="https://prism-ai.dev">Website</a> • 
  <a href="https://docs.prism-ai.dev">Documentation</a> • 
  <a href="https://discord.gg/prism-ai">Community</a>
</div>