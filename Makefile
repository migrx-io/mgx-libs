#                                                                               
# Commonly used targets (see each target for more information):                 
#   run: Build code.                                                            
#   tests: Run tests.                                                           
                                                                                
SHELL := /usr/bin/env bash                                                     
.PHONY: all                                                                     
all: help                                                                       
                                                                                
.PHONY: help
help:
	@echo "make tests - run tests"
	@echo "make run"                                      
                                                                                
.PHONY: run
run:
	${PYENV}/pip3 install --upgrade .

.PHONY: tests
tests:
	find . -type f -name "*.py" |xargs ${PYENV}/python -m yapf -i 
	find . -type f -name "*.py" |xargs ${PYENV}/python -m pylint --unsafe-load-any-extension=y --disable ${PYLINT_OPTS}
	LOGLEVEL=DEBUG mgx_GW_TMP=../mgx-libs/tests/data/apispec.json mgx_FLOWS_DIR="./tests/data/flows" ${PYENV}/python -m pytest -W ignore --alluredir=${ALLURE_RESULTS}
