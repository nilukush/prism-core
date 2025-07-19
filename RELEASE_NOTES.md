# Release Notes

## 🎉 v0.1.0-alpha - Initial Open Source Release (2025-01-19)

We're thrilled to announce that PRISM is now open source! This initial alpha release marks the beginning of our journey as a community-driven project.

### 🚀 What's Included

#### Core Features
- **AI-Powered PRD Generation**: Create comprehensive Product Requirements Documents using Claude 3 Sonnet or GPT-4
- **User Story Creation**: Automatically generate user stories with acceptance criteria
- **Multi-Organization Support**: Manage multiple organizations and projects
- **Role-Based Access Control**: Enterprise-grade security with JWT authentication
- **Real-Time Updates**: WebSocket support for collaborative features

#### Technical Stack
- **Backend**: FastAPI (Python 3.11+) with async support
- **Frontend**: Next.js 14 with TypeScript and Tailwind CSS
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis for session management and caching
- **AI Integration**: Support for OpenAI, Anthropic, and local models

### 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/nilukush/prism-core.git
cd prism-core

# Quick start with Docker
docker compose up -d

# Or install manually
cd backend && pip install -r requirements.txt
cd frontend && npm install
```

### 📝 Known Issues (Alpha)

- Some navigation routes show placeholder content
- AI response times may vary based on provider
- Limited mobile responsiveness in certain views
- Email notifications not yet implemented

### 🛣️ Roadmap

#### Next Release (v0.2.0)
- Jira and Confluence integration
- Enhanced sprint planning features
- Improved mobile experience
- Real-time collaboration features

#### Future Releases
- GitHub/GitLab integration
- Advanced analytics dashboard
- Custom AI model fine-tuning
- Plugin marketplace

### 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:
- Setting up your development environment
- Submitting bug reports and feature requests
- Creating pull requests
- Joining our community discussions

### 📊 Stats

- **Lines of Code**: 15,000+
- **Contributors**: 1 (let's grow this!)
- **License**: MIT
- **Dependencies**: 100% open source

### 🙏 Acknowledgments

Special thanks to:
- The FastAPI and Next.js communities
- Claude and OpenAI for powering our AI features
- All early testers and feedback providers
- You, for being part of our open source journey!

### 📦 Download

- **Source Code**: [GitHub Repository](https://github.com/nilukush/prism-core)
- **Docker Images**: Coming soon on Docker Hub
- **npm Package**: Coming soon

### 🐛 Reporting Issues

Found a bug? Please [create an issue](https://github.com/nilukush/prism-core/issues/new/choose) with:
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Screenshots if applicable

### 📢 Stay Connected

- **GitHub**: [Star and Watch](https://github.com/nilukush/prism-core)
- **Discussions**: [Join the conversation](https://github.com/nilukush/prism-core/discussions)
- **Twitter**: Follow updates at @PrismAI (coming soon)

---

**Note**: This is an alpha release. While the core functionality is stable, you may encounter bugs. Please report any issues to help us improve!

Thank you for trying PRISM! 🚀