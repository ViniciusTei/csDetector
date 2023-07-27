VENV = ./venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

setup: requirements.txt
	python3 -m venv $(VENV)
	chmod +x $(VENV)/bin/activate
	. ./venv/bin/activate
	$(PIP) install -r requirements.txt
	$(PYTHON) -m spacy download en_core_web_sm

venv: requirements.txt
	. ./venv/bin/activate

run: 
	$(PYTHON) csDetector.py -p $(gh_pat) -r "https://github.com/ersilia-os/ersilia" -s "./senti" -o "./out"

run_setup: setup run

alias_extractor:
	$(PYTHON) authorAliasExtractor.py -p $(gh_pat) -r "https://github.com/ersilia-os/ersilia" -d 0.75 -o "./out"

test:
	$(PYTHON) -m pytest --ignore=out

clean:
	$(shell rm -rf venv)
