VENV = ./venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

setup: requirements.txt
	$(PYTHON) -m venv $(VENV)
	chmod +x $(VENV)/bin/activate
	. ./venv/bin/activate
	$(PIP) install -r requirements.txt
	$(PYTHON) -m spacy download en_core_web_sm

venv: requirements.txt
	. ./venv/bin/activate

run: 
	$(PYTHON) csDetector.py -p $(gh_pat) -r "https://github.com/ersilia-os/ersilia" -s "./senti" -o "./out"

run_setup: setup run

clean:
	$(shell rm -rf venv)
