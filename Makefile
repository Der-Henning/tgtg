image:
	docker build -f Dockerfile -t tgtg-scanner:latest .

start:
	docker-compose -f docker-compose.dev.yml up --build

stop:
	docker-compose -f docker-compose.dev.yml down

bash:
	docker-compose -f docker-compose.builder.yml run --rm bash

builder:
	docker-compose -f docker-compose.builder.yml run --rm builder

test:
	docker-compose -f docker-compose.builder.yml run --rm test