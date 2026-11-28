# CLAUDE.md
Project: CMPE 165 Stock Portfolio Suggestion Engine (Henry, Anahi, Chelsea).
Read CONTRACT.md before changing code. Never change a name or signature it defines without the team.

## Commands
- pip install -r requirements.txt
- pytest -q
- pytest -m negative   (one test category: unit, integration, acceptance, negative, or regression)
- pytest --cov=src   (test coverage)
- streamlit run app.py
- python scripts/download_data.py   (only to download the data again)

## Layout
- app.py: the Streamlit screens; the only file that imports streamlit
- src/: models.py, data_loader.py, analysis.py, validation.py, strategy.py, comparison.py
- tests/: one test_<module>.py per module, plus test_app.py
- data/: the saved prices and stock list
- docs/: report, slides, acceptance criteria, test results, calculation check, architecture, AI log

## Rules
- Layered architecture: calls go down only. Keep logic functions pure and small.
- Every change comes with tests, and pytest must pass before a pull request. Each test has one marker from pytest.ini.
- The app never calls an AI API. No passwords or keys in the repository.
- Work on a branch, open a pull request, and log AI help in docs/ai-log.md.
- Explain changes in plain, simple English.
