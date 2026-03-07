SHELL := /bin/bash

.PHONY: up down build logs restart refresh ps shell app-shell init test test-unit test-functional test-e2e test-cov db-init db-migrate db-upgrade db-downgrade user-create

up:
	docker compose up -d --build

down:
	docker compose down

build:
	docker compose build --no-cache

logs:
	docker compose logs -f --tail=150

restart:
	docker compose restart

refresh:
	docker compose down --remove-orphans
	docker compose up -d --build --force-recreate

ps:
	docker compose ps

shell:
	docker compose exec nginx sh

app-shell:
	docker compose exec app sh

init:
	mkdir -p data
	cp -n .env.example .env || true
	@echo "Ambiente inicializado. Edite .env e rode: make up"

test:
	docker compose run --rm app pytest

test-unit:
	docker compose run --rm app pytest -m unit

test-functional:
	docker compose run --rm app pytest -m functional

test-e2e:
	docker compose run --rm app pytest -m e2e

test-cov:
	docker compose run --rm app pytest --cov=app --cov-report=term-missing --cov-report=xml --cov-fail-under=95

db-init:
	docker compose run --rm app flask --app wsgi:app db init

db-migrate:
	docker compose run --rm app flask --app wsgi:app db migrate -m "$(if $(MSG),$(MSG),schema update)"

db-upgrade:
	docker compose run --rm app flask --app wsgi:app db upgrade

db-downgrade:
	docker compose run --rm app flask --app wsgi:app db downgrade

user-create:
	docker compose run --rm app flask --app wsgi:app criar-usuario --email "$(EMAIL)" --senha "$(SENHA)" --papel "$(if $(PAPEL),$(PAPEL),editor)"