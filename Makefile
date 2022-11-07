image:
	docker build -f Dockerfile -t tgtg-scanner:latest .

install:
	pip install -r requirements.dev.txt

start:
	python src/scanner.py

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
	python -m unittest discover -v -s ./src

clean:
	docker-compose -f docker-compose.dev.yml down --remove-orphans
update:
	git add .
	git stash
	git pull
	git stash pop
	docker-compose down
	docker-compose build
	docker-compose up -d
