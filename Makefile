# Poway Recovery Center API: local development (production uses Dockerfile / docker-compose.yml)
PORT ?= 8587
LOG_FILE = /tmp/flask$(PORT).log
VENV = .venv
PYTHON = $(VENV)/bin/python

SHELL = /bin/bash -c
.SHELLFLAGS = -e

default: serve

# Create .venv and install requirements (re-runs only when requirements change)
venv:
	@[ -x $(PYTHON) ] || python3 -m venv $(VENV)
	@if [ ! -f $(VENV)/.install_marker ] || [ requirements.txt -nt $(VENV)/.install_marker ]; then \
		$(PYTHON) -m pip install --timeout 120 --retries 5 -r requirements.txt && touch $(VENV)/.install_marker; \
	fi

# Start the API in the background and wait until it answers
serve: venv stop
	@FLASK_PORT=$(PORT) $(PYTHON) main.py > $(LOG_FILE) 2>&1 &
	@for ((COUNTER = 0; ; COUNTER++)); do \
		if curl -s http://localhost:$(PORT)/ >/dev/null; then \
			echo "API started: http://localhost:$(PORT) (log: $(LOG_FILE))"; break; \
		fi; \
		if [ $$COUNTER -eq 30 ]; then echo "API failed to start:"; cat $(LOG_FILE); exit 1; fi; \
		sleep 1; \
	done

stop:
	@lsof -ti :$(PORT) | xargs kill >/dev/null 2>&1 || true

clean: stop
	@rm -rf $(VENV) __pycache__ */__pycache__

.PHONY: default venv serve stop clean
