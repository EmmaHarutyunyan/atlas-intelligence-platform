.PHONY: up down build logs migrate makemigrations superuser shell test lint format typecheck precommit

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

migrate:
	docker compose exec web python manage.py migrate

makemigrations:
	docker compose exec web python manage.py makemigrations

superuser:
	docker compose exec web python manage.py createsuperuser

shell:
	docker compose exec web python manage.py shell

test:
	docker compose exec web pytest

lint:
	docker compose exec web ruff check .

format:
	docker compose exec web black .
	docker compose exec web ruff check --fix .

typecheck:
	docker compose exec web mypy apps config

precommit:
	pre-commit run --all-files
