VENV = ./venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

run: 
	$(PYTHON) csDetector.py -p $(gh_pat) -r "https://github.com/ersilia-os/ersilia" -s "./senti" -o "./out"

run_web:
	$(PYTHON) webService/csDetectorWebService.py 

test:
	$(PYTHON) -m pytest --ignore=out --pat=$(gh_pat)

clean:
	$(shell rm -rf venv)
