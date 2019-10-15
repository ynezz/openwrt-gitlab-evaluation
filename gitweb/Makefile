VENV_BIN:=.venv/bin
PIP_VENV:=$(VENV_BIN)/pip3
PYTHON_VENV:=$(VENV_BIN)/python3
VENV_PREPARED:=$(VENV_BIN)/.prepared

-include local.mk

all:
	@echo "available make targets:\n"
	@echo "	migrate		migrate projects from gitweb to gitlab"
	@echo ""

migrate: export GITLAB_TOKEN:=$(GITLAB_TOKEN)
migrate: $(VENV_PREPARED)
	@$(PYTHON_VENV) gitweb2gitlab.py

$(VENV_PREPARED): requirements.txt
	python3 -m venv .venv
	$(PIP_VENV) install --upgrade pip
	$(PIP_VENV) install -r $<
	@touch $@

freeze: $(VENV_PREPARED)
	@$(PIP_VENV) freeze --local > requirements.txt

clean:
	@-rm .venv
	@-rm gitweb_index.html
