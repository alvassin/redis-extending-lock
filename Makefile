POETRY_LOCATION=$(shell poetry env info -p)
PROJECT_NAME ?= redis_extending_lock
VERSION = $(shell poetry version --short | tr '+' '-')

all:
	@echo "make devenv    - Configure the development environment"
	@echo "make clean     - Remove generated files"
	@echo "make lint      - Syntax & code style check"
	@echo "make codestyle - Reformat code"
	@echo "make test      - Test this project"
	@echo "make build     - Build packages"
	@exit 0

clean:
	rm -fr *.egg-info .tox dist .mypy_cache .pytest_cache
	find . -iname '*.pyc' -delete

devenv: clean
	rm -rf $(POETRY_LOCATION)
	poetry install

lint:
	poetry check -q
	poetry run pylama .
	poetry run unify --quote "'" --check-only --recursive $(PROJECT_NAME) tests
	poetry run mypy --install-types --non-interactive $(PROJECT_NAME) tests

codestyle:
	poetry run gray *.py redis_extending_lock tests

test: clean lint
	poetry run pytest --cov redis_extending_lock --cov-report term-missing

build: clean
	poetry build
