.PHONY: install test lint typecheck build up up-prod down smoke

install:
	python -m pip install -r requirements-dev.txt
	cd frontend && npm ci

test:
	PYTHONPATH=. pytest

lint:
	ruff check backend
	cd frontend && npm run lint

typecheck:
	cd frontend && npx tsc --noEmit

build:
	cd frontend && npm run build
	docker compose build

up:
	docker compose up --build

up-prod:
	docker compose -f docker-compose.prod.yml up --build -d

down:
	docker compose down
	docker compose -f docker-compose.prod.yml down

smoke:
	curl -fsS http://127.0.0.1:8000/health >/dev/null
	curl -fsS http://127.0.0.1:8000/ready >/dev/null
	@echo "API smoke OK"
