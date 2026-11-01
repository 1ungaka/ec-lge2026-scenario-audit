PYTHON ?= python

.PHONY: setup data baseline freeze lint format test reproduce

setup:
	$(PYTHON) -m pip install -e ".[dev]"

# Downloads the raw IEC files into data/raw/iec and checks them against the manifest.
data:
	$(PYTHON) -m ecaudit.ingest.download --years 2016 2021

# Builds and validates the municipal tables and the crosswalk.
baseline:
	$(PYTHON) -m ecaudit.pipeline baseline

# Rebuilds the frozen prediction sets. The result must hash to the committed value.
freeze:
	$(PYTHON) -m ecaudit.pipeline freeze

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

format:
	$(PYTHON) -m ruff format .

test:
	$(PYTHON) -m pytest

reproduce: data baseline freeze test
