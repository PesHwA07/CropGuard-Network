# Contributing to CropGuard Network

## Getting Started

1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Set up local development** — see the [README](README.md) for prerequisites and Docker Compose setup.

## Code Style

- **Python:** Format with Black, sort imports with isort
  ```bash
  black backend/ spark_jobs/ rag_service/
  isort backend/ spark_jobs/ rag_service/
  ```
- **React/JS:** Format with Prettier, lint with ESLint
  ```bash
  cd frontend && npx prettier --write src/ && npx eslint src/
  ```

## Pull Request Process

1. **Write tests** for any new endpoint, model change, or Spark job before opening a PR.
2. **Run the test suite locally** before pushing:
   ```bash
   cd backend && pytest tests/ -v
   ```
3. **Open a Pull Request** with a clear description and link to any related issue.
4. **CI must pass** before merge.
5. For model/dataset changes, document evaluation metrics (mAP, precision, recall) before and after in the PR description.

## Commit Message Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation
- `infra:` — infrastructure / DevOps
- `test:` — tests
- `refactor:` — code restructuring without behavior change
- `chore:` — maintenance (deps, config)

## Reporting Issues

Open an issue with:
- Steps to reproduce
- Expected vs actual behavior
- Environment (OS, Python version, Docker version)
- Relevant logs
