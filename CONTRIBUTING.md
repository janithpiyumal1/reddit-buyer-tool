# Contributing to Reddit Buyer Tool

Thank you for your interest in contributing to the Reddit Buyer Tool! This document provides guidelines and instructions for contributing.

## 🎯 Ways to Contribute

- **Bug Reports**: Report issues you encounter
- **Feature Requests**: Suggest new features or improvements
- **Code Contributions**: Submit bug fixes or new features
- **Documentation**: Improve README, code comments, or guides
- **Testing**: Add or improve test coverage
- **Examples**: Share usage examples or case studies

## 🐛 Reporting Bugs

Before submitting a bug report:
1. Check existing issues to avoid duplicates
2. Verify you're using the latest version
3. Test with a clean environment

Include in your bug report:
- Clear title and description
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Relevant logs or error messages

## 💡 Suggesting Features

For feature requests:
1. Check if it aligns with project goals
2. Describe the problem it solves
3. Provide use cases and examples
4. Consider backward compatibility

## 🔧 Development Setup

1. Fork the repository
2. Clone your fork:
```bash
git clone https://github.com/YOUR_USERNAME/reddit-buyer-tool.git
cd reddit-buyer-tool
```

3. Set up development environment:
```bash
# Backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r backend/requirements.txt

# Frontend
cd frontend
npm install
```

4. Create a branch:
```bash
git checkout -b feature/your-feature-name
```

## 📝 Code Style

### Python (Backend)

- Follow PEP 8
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions focused and small
- Use meaningful variable names

Example:
```python
def classify_post(title: str, body: str) -> Tuple[bool, float, str]:
    """
    Classify a Reddit post as buyer/not-buyer.
    
    Args:
        title: Post title
        body: Post body text
        
    Returns:
        Tuple of (is_buyer, confidence_score, reason)
    """
    # Implementation
```

### JavaScript (Frontend)

- Use functional components with hooks
- Use meaningful component and variable names
- Keep components small and focused
- Add PropTypes or TypeScript types

Example:
```javascript
function PostsTable({ posts, loading, onPostUpdated }) {
  // Component logic
}
```

## 🧪 Testing

All code contributions must include tests.

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### Writing Tests

- Add tests in `backend/tests/`
- Test both success and error cases
- Use descriptive test names
- Mock external dependencies (Reddit API, OpenAI)

Example:
```python
def test_classify_buyer_post():
    """Test that buyer posts are correctly classified."""
    text = "Looking for a web developer to hire"
    is_buyer, score, reason = classify_text(text)
    
    assert is_buyer == True
    assert score > 0.5
```

## 📋 Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Run tests** and ensure they pass
4. **Update CHANGELOG** with your changes
5. **Commit with meaningful messages**:
   ```
   feat: add subreddit analytics dashboard
   fix: handle empty post bodies in classifier
   docs: update API endpoint documentation
   test: add edge cases for LLM classifier
   ```

6. **Push to your fork** and submit a PR
7. **Address review feedback** promptly

### Pull Request Template

```markdown
## Description
Brief description of what this PR does

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
How has this been tested?

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guidelines
- [ ] All tests pass
```

## 🎨 Coding Standards

### Backend Structure

```
backend/app/
├── main.py          # FastAPI app entry point
├── routes.py        # API endpoints
├── models.py        # Pydantic models
├── db.py            # Database operations
├── deps.py          # Dependencies and config
├── classifier.py    # Classification logic
└── reddit_fetcher.py # Reddit API client
```

### Frontend Structure

```
frontend/src/
├── components/      # React components
├── api.js          # API client
├── App.jsx         # Main app component
└── main.jsx        # Entry point
```

## 🏷️ Commit Message Guidelines

Use conventional commits:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Formatting
- `refactor:` - Code restructuring
- `test:` - Tests
- `chore:` - Maintenance

Examples:
```
feat: add email notification for new leads
fix: resolve MySQL connection pool exhaustion
docs: add API usage examples to README
test: increase classifier test coverage to 90%
```

## 🔍 Code Review

All submissions require review. We look for:

- **Correctness**: Does it work as intended?
- **Testing**: Are there adequate tests?
- **Maintainability**: Is the code clear and well-structured?
- **Performance**: Are there any bottlenecks?
- **Security**: Are there any vulnerabilities?
- **Documentation**: Is it well-documented?

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors will be acknowledged in:
- README.md Contributors section
- Release notes
- Project documentation

## 💬 Questions?

- Open a discussion on GitHub
- Check existing issues and PRs
- Review the README and documentation

Thank you for contributing! 🎉
