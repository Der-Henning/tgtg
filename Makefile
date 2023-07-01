image:
	docker build -f Dockerfile -t tgtg-scanner:latest .

install:
	poetry install

start:
	python src/main.py -d

executable:
	rm -r ./build ||:
	rm -r ./dist ||:
	poetry run pyinstaller ./scanner.spec
	cp ./src/config.sample.ini ./dist/config.ini
	zip -j ./dist/scanner.zip ./dist/*

test:
	poetry run pytest -v -m "not tgtg_api" --cov src/

lint:
	poetry run pre-commit run -a
