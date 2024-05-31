setup: install just-build package-force-reinstall

setup-linux: install just-build package-force-reinstall-linux

dev:
	poetry run flask --app page_analyzer:app run

debug:
	poetry run flask --app page_analyzer:app --debug run

PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

install:
	poetry install

just-build:
	poetry build

lint:
	poetry run flake8 page_analyzer

selfcheck:
	poetry check

check: selfcheck test lint

build: check
	poetry build

package-install:
	python -m pip install --user dist/*.whl

remove-envs:
	rm -rf .venv && poetry env remove --all

package-force-reinstall:
	python -m pip install --user --force-reinstall dist/*.whl

package-force-reinstall-linux:
	python3 -m pip install --user --force-reinstall dist/*.whl