PYTHON ?= python3
VENV ?= venv
VENV_PYTHON = $(VENV)/bin/python
VENV_PIP = $(VENV)/bin/pip

.PHONY: install test api ui lint docker-build docker-up docker-down

install:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements.txt

test:
	$(VENV_PYTHON) -m pytest -q

api:
	$(VENV_PYTHON) fastapi_api.py

ui:
	$(VENV)/bin/streamlit run streamlit_ui.py

lint:
	. $(VENV)/bin/activate && $(PYTHON) -m compileall .

docker-build:
	docker compose build

docker-up:
	docker compose up

docker-down:
	docker compose down

