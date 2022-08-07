SHELL = /bin/bash
run:
	source .env \
	&& ./venv/bin/python main.py

install:
	source .env \
	&& ./venv/bin/pip install -r requirements.txt

install-dev:
	source .env \
	&& ./venv/bin/pip install -r requirements-dev.txt

fmt:
	source .env \
	&& ./venv/bin/black .

lint:
	source .env \
	&& ./venv/bin/flake8 .
