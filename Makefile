image:
	docker build -f Dockerfile -t tgtg-scanner:latest .

start:
	python src/scanner.py

bash:
	docker-compose -f docker-compose.dev.yml build
	docker-compose -f docker-compose.dev.yml run --rm bash

executable:
	pyinstaller scanner.spec

test:
	python -m unittest discover -v -s ./src

clean:
	docker-compose -f docker-compose.dev.yml down --remove-orphans