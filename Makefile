.PHONY: install test lint run form-worker
install:
	python -m pip install -e '.[dev]'

test:
	pytest -q

lint:
	ruff check src tests

run:
	uvicorn scheme_navigator.api.main:app --reload

form-worker:
	python -m scheme_navigator.workers.mock_form_worker --profile data/demo/citizen_profile.json
