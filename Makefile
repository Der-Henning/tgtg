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
	@if which python3 >/dev/null 2>&1; then \
        python3 -m pytest -v -m "not tgtg_api" --cov src/; \
    else \
        python -m pytest -v -m "not tgtg_api" --cov src/; \
    fi

lint:
	pre-commit run -a

clean:
	docker-compose -f docker-compose.dev.yml down --remove-orphans
