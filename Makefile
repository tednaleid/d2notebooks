test:
	python -m unittest discover -s tests

lint:
	ruff check

check: test lint