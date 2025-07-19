# PRISM Project Structure

This document provides an overview of the PRISM repository structure after the open source release.

## 📁 Repository Overview

```
prism-core/
├── .github/                    # GitHub configuration
│   ├── workflows/             # GitHub Actions CI/CD
│   ├── ISSUE_TEMPLATE/        # Issue templates
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── dependabot.yml
│   ├── CODEOWNERS
│   └── labeler.yml
│
├── backend/                   # FastAPI backend application
│   ├── src/                  # Source code
│   │   ├── api/             # API endpoints
│   │   ├── core/            # Core functionality
│   │   ├── models/          # Database models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── main.py          # Application entry point
│   ├── tests/               # Test files
│   ├── alembic/             # Database migrations
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Backend container
│
├── frontend/                 # Next.js frontend application
│   ├── src/                 # Source code
│   │   ├── app/            # Next.js app directory
│   │   ├── components/      # React components
│   │   ├── lib/            # Utilities and helpers
│   │   └── styles/         # CSS and styling
│   ├── public/             # Static assets
│   ├── package.json        # Node dependencies
│   └── Dockerfile          # Frontend container
│
├── docker/                   # Docker configuration
│   ├── postgres/           # PostgreSQL setup
│   └── redis/              # Redis configuration
│
├── k8s/                     # Kubernetes manifests
│   ├── base/               # Base configurations
│   ├── overlays/           # Environment-specific configs
│   └── argocd/             # ArgoCD application definitions
│
├── helm/                    # Helm charts
│   └── prism/              # PRISM Helm chart
│
├── scripts/                 # Development and utility scripts
│   ├── dev-start.sh        # Start development environment
│   ├── dev-stop.sh         # Stop development environment
│   ├── quick-start.sh      # Quick setup script
│   ├── seed_data.py        # Database seeding
│   └── configure_ai.sh     # AI provider configuration
│
├── docs/                    # Documentation
│   ├── api/                # API documentation
│   ├── architecture/       # Architecture guides
│   └── technical/          # Technical documentation
│
├── .env.example            # Environment variables template
├── docker-compose.yml      # Docker Compose configuration
├── README.md               # Project overview
├── CONTRIBUTING.md         # Contribution guidelines
├── LICENSE                 # MIT License
├── CHANGELOG.md            # Version history
├── RELEASE_NOTES.md        # Release information
└── ANNOUNCEMENT.md         # Open source announcement
```

## 🔑 Key Directories

### `/backend`
The Python FastAPI backend containing:
- RESTful API endpoints
- Database models and migrations
- Business logic and AI integrations
- Authentication and authorization

### `/frontend`
The Next.js 14 frontend with:
- Modern React components
- TypeScript for type safety
- Tailwind CSS for styling
- Responsive design

### `/k8s` and `/helm`
Production-ready deployment configurations:
- Kubernetes manifests for cloud deployment
- Helm charts for easy installation
- Multi-environment support

### `/scripts`
Helpful scripts for:
- Development environment setup
- Database initialization
- AI provider configuration
- Testing and validation

## 📝 Important Files

- **.env.example**: Template for environment variables
- **docker-compose.yml**: Local development setup
- **requirements.txt**: Python dependencies
- **package.json**: Node.js dependencies
- **CONTRIBUTING.md**: How to contribute
- **LICENSE**: MIT license terms

## 🚀 Getting Started

1. Clone the repository
2. Copy `.env.example` to `.env`
3. Run `docker compose up -d`
4. Access the application at `http://localhost:3100`

For detailed setup instructions, see the [README.md](../README.md).

## 🤝 Contributing

We welcome contributions! Please read [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on:
- Setting up your development environment
- Making changes
- Submitting pull requests
- Following our coding standards

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.