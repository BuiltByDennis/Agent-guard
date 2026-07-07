# Contributing to Vigilance Operations AI Agent Proxy

First off, thank you for considering contributing to Vigilance Operations! It's people like you that make the open-source community such an amazing place to learn, inspire, and create.

This document provides guidelines and instructions for contributing to this repository.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [How to Contribute](#how-to-contribute)
    - [Reporting Bugs](#reporting-bugs)
    - [Suggesting Enhancements](#suggesting-enhancements)
    - [Pull Requests](#pull-requests)
4. [Development Setup](#development-setup)
5. [Styleguides](#styleguides)
    - [Git Commit Messages](#git-commit-messages)
    - [Python Code Style](#python-code-style)
6. [Getting Help](#getting-help)

## Code of Conduct

This project and everyone participating in it is governed by a standard Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to [dennyaaba@gmail.com](mailto:dennyaaba@gmail.com).

## Getting Started

Before you begin:
- Check out the [README.md](README.md) for a high-level overview of the project architecture and features.
- Review existing Issues to ensure your idea or bug hasn't already been reported.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue. A great bug report should include:
- A clear and descriptive title.
- Steps to reproduce the issue.
- Expected behavior vs. actual behavior.
- Environment details (OS, Python version, Docker version, etc.).
- Logs or screenshots if applicable.

### Suggesting Enhancements

We are always looking to improve our features, especially around security, telemetry, and rate-limiting. When suggesting an enhancement:
- Explain why this enhancement would be useful to most users.
- Provide examples of how it would work or code snippets if you have them.

### Pull Requests

1. **Fork the repo** and create your branch from `main`.
2. **Write code** following the styleguides below.
3. **Add tests** if you are adding new functionality.
4. **Update documentation** (README, comments) if your changes affect how the system is deployed or used.
5. **Ensure the test suite passes** before submitting your PR.
6. **Open a Pull Request** with a detailed description of what you changed and why.

## Development Setup

To set up the project locally for development:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/your-repo.git
   cd your-repo
   ```

2. **Environment Variables:**
   Copy the example environment file and configure it for local development.
   ```bash
   cp .env.example .env
   ```

3. **Docker Compose:**
   Start the local database and Redis services using Docker Compose:
   ```bash
   docker-compose up -d db redis
   ```

4. **Python Environment:**
   We recommend using a virtual environment.
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Run the Backend:**
   ```bash
   uvicorn main:app --reload
   ```

## Styleguides

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature").
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...").
- Limit the first line to 72 characters or less.
- Reference issues and pull requests liberally after the first line.

### Python Code Style

- We follow standard **PEP 8** guidelines.
- Use `black` for code formatting.
- Use `flake8` for linting.
- Ensure type hints are used extensively throughout the FastAPI backend.

## Getting Help

If you need help or have questions regarding a contribution, feel free to reach out via email at [dennyaaba@gmail.com](mailto:dennyaaba@gmail.com) or open a discussion in the repository.
