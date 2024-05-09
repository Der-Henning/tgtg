clean:
	rm -rf .venv .pytest_cache .tox .mypy_cache dist build

install:
	poetry install
	poetry run pre-commit install --install-hooks

server:
	poetry run tgtg_server

start:
	poetry run scanner -d --base_url http://localhost:8080

test:
	poetry run pytest -v -m "not tgtg_api" --cov=tgtg_scanner

lint:
	poetry run pre-commit run -a

tox:
	tox

executable:
	rm -rf ./build ./dist
	poetry run pyinstaller ./scanner.spec
	cp ./config.sample.ini ./dist/scanner/config.ini
	cd ./dist/scanner; zip -r ../scanner.zip *

images:
	docker build -f ./docker/Dockerfile -t tgtg-scanner:latest .
	docker build -f ./docker/Dockerfile.alpine -t tgtg-scanner:latest-alpine .
