# Contributing to ATEMS

## Development Setup

1. Clone the repo and `cd atems`
2. Create venv: `python3 -m venv .venv && source .venv/bin/activate`
3. Install: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and set `SQLALCHEMY_DATABASE_URI`, `SECRET_KEY`

## Running

- `export FLASK_APP=atems:create_app`
- `flask db upgrade`
- `python scripts/seed_user.py` (creates admin / admin123)
- `python atems.py` or `gunicorn -c gunicorn.conf.py "atems:create_app()"`

## Testing

- `pytest` — Backend tests
- See [ROADMAP.md](ROADMAP.md) and [docs/ATEMS_TEST_REPORT.md](docs/ATEMS_TEST_REPORT.md)

## Code Standards

- Python: type hints, docstrings for public APIs
- Flask: follow project patterns in routes, models, forms

## Documentation

- Add/update docs in `docs/`
- Update [docs/INDEX.md](docs/INDEX.md) for new topics
- Completion reports go in `docs/archive/`

## Pull Requests

1. Branch from `main` (or current dev branch)
2. Run tests before submitting
3. Keep PRs focused; link related issues
