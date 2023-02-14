image:
	docker build -f Dockerfile -t tgtg-scanner:latest .

install:
	pip install -r requirements-dev.txt

start:
	python src/main.py

bash:
	docker-compose -f docker-compose.dev.yml build
	docker-compose -f docker-compose.dev.yml run --rm bash

executable:
	rm -r build ||:
	rm -r dist ||:
	pyinstaller scanner.spec
	cp src/config.sample.ini dist/config.ini
	zip -j dist/scanner.zip dist/*

test:
	python -m pytest -v -m "not tgtg_api" --cov src/

lint:
	pre-commit run -a

clean:
	docker-compose -f docker-compose.dev.yml down --remove-orphans
