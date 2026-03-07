SHELL := /bin/bash

.PHONY: up down build logs restart refresh ps shell app-shell init

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