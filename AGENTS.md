# Repository Guidelines

## Project Structure & Module Organization
- `main.py` is the entry point for sync flows.
- `application/` contains use cases (orchestration logic).
- `domain/` contains entities, ports (interfaces), and constants.
- `infrastructure/` contains adapters for Dynamics, MySQL, and Azure AD.
- `config/` holds settings and logging configuration.
- `utils/` holds validators and data transformers.
- `database/` holds SQL schemas and bootstrap scripts.
- `scripts/` contains operational and diagnostic utilities.
- `examples/` contains sample usage scripts.
- `env.example` is the template for local configuration.

## Build, Test, and Development Commands
- `pip install -r requirements.txt` installs dependencies.
- `cp env.example .env` creates the local environment file.
- `mysql -u root -p < database/create_database.sql` initializes MySQL schema.
- `python scripts/initialize_db.py` initializes schema via Python.
- `python scripts/check_environment.py` validates config, deps, and connectivity.
- `python main.py` runs full synchronization.
- `python main.py CompanyATISAs` syncs a single entity.
- `python scripts/diagnose_integration.py` runs end-to-end integration checks.

## Coding Style & Naming Conventions
- Follow existing Python style: 4-space indentation, PEP 8 conventions.
- Use `snake_case` for functions/variables, `PascalCase` for classes, and
  `UPPER_SNAKE_CASE` for constants (see `domain/constants.py`).
- Keep logic aligned with the hexagonal layers (domain → application → infrastructure).
- Reuse shared validators/transformers in `utils/` instead of duplicating logic.

## Testing Guidelines
- There is no formal pytest suite in this repo.
- Use script-based checks for validation:
  - `scripts/check_environment.py` for config and connectivity.
  - `scripts/diagnose_integration.py` for integration smoke tests.
  - `scripts/test_onboarding_fields.py` for mapping validation.
- If you add tests, place them under `scripts/` or introduce a `tests/` directory
  consistently.

## Commit & Pull Request Guidelines
- Commit messages are short and descriptive with no strict prefix convention
  (see `git log` for examples); keep them to one line.
- PRs should include:
  - Clear summary of changes and affected entities.
  - Steps to validate (commands run and outcomes).
  - Notes on schema/config changes (`database/`, `env.example`).
  - Confirmation that no secrets were committed (`.env` stays local).

## Security & Configuration Tips
- Do not commit `.env`; use `env.example` for defaults.
- Store Azure AD and DB credentials only in environment variables.
- Validate connectivity with `scripts/check_environment.py` before syncing.
