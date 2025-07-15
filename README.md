# PRISM - AI-Powered Product Management Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)

## 🚀 Overview

PRISM is an enterprise-grade, AI-powered product management platform that revolutionizes how teams build products. By leveraging advanced AI capabilities, PRISM automates routine PM tasks, provides intelligent insights, and accelerates the product development lifecycle.

### Key Features

- **🤖 AI-Powered PRD Generation**: Generate comprehensive Product Requirements Documents using Claude 3 Sonnet
- **📝 Intelligent User Story Creation**: Convert requirements into detailed user stories with acceptance criteria
- **📊 Sprint Planning & Analytics**: AI-driven sprint estimation and velocity analysis
- **🔄 Real-time Collaboration**: Team workspaces with role-based access control
- **🔐 Enterprise Security**: JWT authentication, session persistence, and audit logging
- **🎯 Multi-Provider AI Support**: OpenAI, Anthropic, and local models via Ollama
- **📈 Predictive Analytics**: Forecast sprint completion and identify bottlenecks

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Next.js 14    │────▶│   FastAPI       │────▶│  PostgreSQL     │
│   Frontend      │     │   Backend       │     │   Database      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                          │
                               ├──────────────────────────┤
                               ▼                          ▼
                        ┌─────────────┐           ┌─────────────┐
                        │    Redis    │           │   Qdrant    │
                        │    Cache    │           │ Vector Store│
                        └─────────────┘           └─────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)
- 4GB+ RAM recommended

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/prism-core.git
cd prism-core
```

### 2. Configure Environment

```bash
# Copy environment templates
cp .env.example .env
cp frontend/.env.example frontend/.env.local

# Configure AI provider (optional - uses mock by default)
./configure_ai.sh
```

### 3. Start the Application

```bash
# Build and start all services
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Start frontend development server
cd frontend
npm install
npm run dev
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8100
- **API Documentation**: http://localhost:8100/docs

### Default Credentials

```
Email: nilukush@gmail.com
Password: Test123!@#
```

## 📚 Documentation

- [Setup Guide](./SETUP_GUIDE.md) - Quick start and installation instructions
- [Architecture Overview](./ARCHITECTURE.md) - System design and components
- [API Documentation](http://localhost:8100/docs) - Interactive API explorer
- [Contributing Guide](./CONTRIBUTING.md) - How to contribute to PRISM

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI with async/await
- **Database**: PostgreSQL 16 with SQLAlchemy
- **Cache**: Redis 7 for sessions and rate limiting
- **AI Integration**: Multi-provider support (OpenAI, Anthropic, Ollama)
- **Task Queue**: Celery with Redis broker
- **Security**: JWT auth, rate limiting, DDoS protection

### Frontend
- **Framework**: Next.js 14 with App Router
- **UI Library**: shadcn/ui with Tailwind CSS
- **State Management**: React Context + Hooks
- **Authentication**: NextAuth.js
- **Forms**: React Hook Form with Zod validation

### Infrastructure
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Kubernetes-ready with Helm charts
- **CI/CD**: GitHub Actions with security scanning
- **Monitoring**: Prometheus metrics + OpenTelemetry

## 🔒 Security Features

- **Authentication**: JWT tokens with refresh rotation
- **Session Management**: Redis-backed persistent sessions
- **Rate Limiting**: Token bucket algorithm per endpoint
- **DDoS Protection**: 6-layer defense system
- **Input Validation**: Comprehensive sanitization
- **Audit Logging**: Complete activity tracking

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for details.

### Development Setup

```bash
# Backend development
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn src.main:app --reload

# Frontend development
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
npm run test:e2e
```

## 📊 Project Status

- ✅ Core product management features
- ✅ AI integration (PRD, user stories)
- ✅ Authentication & authorization
- ✅ Real-time collaboration
- 🚧 Advanced analytics dashboard
- 🚧 Mobile application
- 📋 Plugin marketplace

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- UI components from [shadcn/ui](https://ui.shadcn.com/)
- AI powered by [Anthropic Claude](https://www.anthropic.com/)
- Inspired by modern product management best practices

## 📞 Support

- 📧 Email: support@prism-ai.dev
- 💬 Discord: [Join our community](https://discord.gg/prism)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/prism-core/issues)

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/prism-core&type=Date)](https://star-history.com/#yourusername/prism-core&Date)

---

<p align="center">Made with ❤️ by the PRISM Team</p>