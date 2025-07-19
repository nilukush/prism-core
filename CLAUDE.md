# CLAUDE.md - PRISM Development Reference

This file provides context for Claude AI when working with the PRISM codebase.

## 🎉 Current Status: Open Source Released!

PRISM is now fully open source (v0.1.0-alpha) as of January 19, 2025. The repository is public and accepting contributions.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/nilukush/prism-core.git
cd prism-core

# Start with Docker
docker compose up -d

# Access the application
Frontend: http://localhost:3100
Backend: http://localhost:8100
API Docs: http://localhost:8100/docs
```

## 📁 Project Structure

```
prism-core/
├── backend/          # FastAPI backend
├── frontend/         # Next.js 14 frontend
├── docker/          # Docker configurations
├── k8s/            # Kubernetes manifests
├── helm/           # Helm charts
├── scripts/        # Development scripts
├── docs/           # Documentation
└── .github/        # GitHub workflows
```

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy
- **Cache**: Redis
- **AI**: OpenAI, Anthropic Claude, Ollama support
- **Auth**: JWT with session persistence

### Frontend
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **State**: React Context + SWR
- **Auth**: NextAuth.js

## 🔧 Common Development Tasks

### Running Tests
```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test
```

### Database Migrations
```bash
# Create migration
cd backend && alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Adding New Features
1. Create feature branch from `main`
2. Implement backend API endpoint
3. Add frontend UI components
4. Write tests
5. Update documentation
6. Submit PR

## 🏗️ Architecture Overview

### Multi-tenant Structure
```
Organization (1) → Projects (N) → PRDs/Stories (N)
```

### AI Agent System
- BaseAgent: Abstract class for all agents
- StoryAgent: Generates user stories
- PRDAgent: Creates PRDs
- Configurable LLM providers per agent

### API Structure
```
/api/v1/
├── auth/          # Authentication
├── organizations/ # Organization management
├── projects/      # Project CRUD
├── documents/     # PRDs and stories
└── ai/           # AI operations
```

## 📝 Code Style Guidelines

### Python (Backend)
- Use type hints
- Follow PEP 8
- Async/await for I/O operations
- Pydantic for validation

### TypeScript (Frontend)
- Strict mode enabled
- Functional components
- Custom hooks for logic
- Proper error boundaries

## 🚧 Known Issues (v0.1.0-alpha)

1. Some navigation routes show placeholders
2. Email notifications not implemented
3. Limited mobile responsiveness
4. WebSocket features pending

## 🔄 Current Development Focus

### Completed ✅
- Core AI integration
- Multi-organization support
- JWT authentication
- Docker deployment
- Open source release

### In Progress 🚧
- Jira/Confluence integration
- Real-time collaboration
- Mobile optimization
- Performance improvements

### Planned 📋
- Plugin system
- Advanced analytics
- Desktop/mobile apps
- Marketplace

## 🤝 Contributing

When helping with contributions:
1. Check existing issues first
2. Follow CONTRIBUTING.md guidelines
3. Ensure tests pass
4. Update relevant documentation
5. Use conventional commits

## 🔐 Security Considerations

- Never commit .env files
- Use environment variables for secrets
- Validate all user inputs
- Follow OWASP guidelines
- Report security issues privately

## 📊 Performance Guidelines

- Lazy load large components
- Use Redis for caching
- Paginate large datasets
- Optimize database queries
- Monitor API response times

## 🐛 Debugging Tips

### Backend
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Check database connection
docker compose exec backend python -c "from src.core.database import engine; print(engine)"
```

### Frontend
```bash
# Debug Next.js
npm run dev -- --inspect

# Check API connectivity
curl http://localhost:8100/api/v1/health
```

## 📚 Useful Resources

- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Next.js Docs](https://nextjs.org/docs)
- [Project Wiki](https://github.com/nilukush/prism-core/wiki)
- [API Reference](http://localhost:8100/docs)

## 🌟 Repository Information

- **GitHub**: https://github.com/nilukush/prism-core
- **License**: MIT
- **Version**: 0.1.0-alpha
- **Status**: Actively maintained
- **Contributors**: Welcome!

---

**Note**: This file is for AI assistance and development reference. For user documentation, see README.md.