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
	$(PYTHON) csDetector.py -p "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" -r "https://github.com/ersilia-os/ersilia" -s "./senti" -o "./out"

run_setup: setup run

clean:
	$(shell rm -rf venv)
