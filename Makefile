image:
	docker build -f docker/Dockerfile .

start-dev:
	docker-compose -f docker-compose.dev.yml up --build

stop-dev:
	docker-compose -f docker-compose.dev.yml down

bash:
	docker-compose -f docker-compose.builder.yml run --rm bash

builder:
	docker-compose -f docker-compose.builder.yml run --rm builder