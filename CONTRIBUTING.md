# Contributing to RedisVL Classifier Router

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/RedisVLClassifierRouter.git
   cd RedisVLClassifierRouter
   ```
3. **Set up the development environment**:
   ```bash
   uv sync
   source .venv/bin/activate
   ```

## Development Setup

### Prerequisites

- Python 3.11+
- Redis Stack (with RedisSearch)
- uv package manager
- OpenAI API key

### Install Dependencies

```bash
# Install all dependencies including dev tools
uv sync --all-extras
```

### Running Tests

```bash
# Run all scripts to verify functionality
python 1_baseline_with_openai.py
python 2_RedisVLRouter.py
python 3_RedisVLRouterwithChatGPT.py
python 4_RedisVLRouterWithOptimizer.py
```

## Making Changes

### Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring

Example: `feature/add-new-aggregation-method`

### Code Style

We use `ruff` for linting and formatting:

```bash
# Format code
ruff format .

# Check for issues
ruff check .
```

### Commit Messages

Follow conventional commits format:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

Example: `feat: add support for custom distance metrics`

## Pull Request Process

1. **Update documentation** if needed
2. **Test your changes** thoroughly
3. **Update README.md** if adding new features
4. **Create a pull request** with a clear description
5. **Link any related issues**

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] No API keys or secrets in code

## Areas for Contribution

### High Priority

- [ ] Add unit tests for core functions
- [ ] Improve error handling
- [ ] Add support for more distance metrics
- [ ] Performance optimizations
- [ ] Better logging and debugging

### Documentation

- [ ] Add more examples
- [ ] Create tutorial videos
- [ ] Improve API documentation
- [ ] Add troubleshooting guide

### Features

- [ ] Support for other datasets
- [ ] Web UI for visualization
- [ ] Real-time classification API
- [ ] Batch processing support
- [ ] Multi-language support

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Collaborate openly

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Publishing private information
- Unprofessional conduct

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Check existing issues before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉

