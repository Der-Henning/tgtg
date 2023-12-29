
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

executable:
	rm -r ./build ||:
	rm -r ./dist ||:
	poetry run pyinstaller ./scanner.spec
	cp ./config.sample.ini ./dist/config.ini
	zip -j ./dist/scanner.zip ./dist/*

images:
	docker build -f ./docker/Dockerfile -t tgtg-scanner:latest .
	docker build -f ./docker/Dockerfile.alpine -t tgtg-scanner:latest-alpine .
