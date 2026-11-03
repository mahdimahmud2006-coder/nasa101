PYTHON ?= .venv/bin/python
UV ?= uv
.PHONY: setup inspect process augment timeseries validate-timeseries test validate demo context download-context validate-context
setup:
	$(UV) --cache-dir .uv-cache venv .venv --python python3
	$(UV) --cache-dir .uv-cache pip install --python $(PYTHON) -r requirements.txt
inspect:
	$(PYTHON) -m src.ingest.inspect_h5 . > data/derived/audit.txt
process:
	$(PYTHON) -m src.compute.pipeline --config config.json
	$(PYTHON) -m src.compute.extend_evidence
augment:
	$(PYTHON) -m src.compute.extend_evidence
timeseries:
	$(PYTHON) -m src.compute.timeseries_pipeline --config config.timeseries.json
validate-timeseries:
	$(PYTHON) -m src.compute.validate_timeseries
test:
	$(PYTHON) -m pytest -q
validate:
	$(PYTHON) -m src.compute.validate
demo:
	OFFLINE=1 $(PYTHON) -m src.api.app

download-context:
	$(PYTHON) -m src.ingest.environment
context:
	$(PYTHON) -m src.compute.context_pipeline --config config.context.json
validate-context:
	$(PYTHON) -m src.compute.validate_context

.PHONY: test-ui
test-ui:
	node tests/navigation.test.mjs
	node tests/home.test.mjs
	node tests/playback.test.mjs
	node tests/terrain-view.test.mjs
	node tests/studio.test.mjs
	node tests/change-lab.test.mjs
	node tests/investigation-model.test.mjs
	node tests/investigations.test.mjs
	node tests/time-axis.test.mjs
	node tests/dualpol.test.mjs
	node tests/reasoning.test.mjs
	node tests/investigation-state.test.mjs
	node tests/expanded.test.mjs
	node tests/expanded-controller.test.mjs

.PHONY: flood thermal download-thermal studio validate-flood
flood:
	$(PYTHON) -m src.compute.flood_pipeline
thermal:
	$(PYTHON) -m src.compute.thermal_pipeline
download-thermal:
	$(PYTHON) -m src.ingest.thermal
studio: flood thermal
validate-flood:
	$(PYTHON) -m src.compute.validate_flood

.PHONY: dna landslide change-lab validate-change-lab
dna:
	$(PYTHON) -m src.compute.dna_pipeline
landslide:
	$(PYTHON) -m src.compute.landslide_pipeline
change-lab: dna landslide
validate-change-lab:
	$(PYTHON) -m src.compute.validate_change_lab

.PHONY: download-landslide-reference
download-landslide-reference:
	$(PYTHON) -m src.ingest.landslide_reference

.PHONY: run check-ready verify release
run:
	./run.sh
check-ready:
	$(PYTHON) -m src.api.readiness
verify: test test-ui validate validate-timeseries validate-context validate-flood validate-change-lab validate-investigations validate-dualpol validate-context-v2 validate-dna-v2 validate-references validate-interferometry-gate validate-expanded check-ready check-web
release:
	$(PYTHON) scripts/package_release.py

.PHONY: check-web
check-web:
	$(PYTHON) scripts/check_web.py

.PHONY: investigations jamuna wetland validate-investigations
investigations:
	$(PYTHON) -m src.compute.investigation_pipeline
jamuna:
	$(PYTHON) -m src.compute.investigation_pipeline --case jamuna_river
wetland:
	$(PYTHON) -m src.compute.investigation_pipeline --case tanguar_wetland
validate-investigations:
	$(PYTHON) -m src.compute.validate_investigations

# Optional metadata acquisition, isolated from runtime and standard verification.
.PHONY: setup-search search-slots publish-time-axis check-baseline
SEARCH_PYTHON ?= .venv-search/bin/python
SLOT_OUTPUT ?= data/candidates/phase1_2026_11_02_final
setup-search:
	$(UV) --cache-dir .uv-cache venv .venv-search --python $(PYTHON)
	$(UV) --cache-dir .uv-cache pip install --python $(SEARCH_PYTHON) -r requirements-search.txt
search-slots:
	$(SEARCH_PYTHON) scripts/nisar_slot_search.py --output "$(SLOT_OUTPUT)"
publish-time-axis:
	$(PYTHON) scripts/publish_time_axis.py --source "$(SLOT_OUTPUT)"
check-baseline:
	$(PYTHON) scripts/freeze_baseline.py --check

.PHONY: dualpol validate-dualpol
dualpol:
	$(PYTHON) -m src.compute.dualpol_pipeline
validate-dualpol:
	$(PYTHON) -m src.compute.validate_dualpol

.PHONY: validate-context-v2
validate-context-v2:
	$(PYTHON) -m src.compute.validate_context_v2

.PHONY: validate-dna-v2 claims-check
validate-dna-v2:
	$(PYTHON) -m src.compute.validate_investigation_dna
claims-check:
	$(PYTHON) scripts/generate_claims.py --check

.PHONY: validate-references
validate-references:
	$(PYTHON) -m src.compute.validate_references

.PHONY: validate-interferometry-gate
validate-interferometry-gate:
	$(PYTHON) -m src.compute.validate_interferometry_gate

.PHONY: expanded validate-expanded
expanded:
	$(PYTHON) -m src.compute.expanded_record
validate-expanded:
	$(PYTHON) -m src.compute.validate_expanded_record

.PHONY: bangladesh-record validate-bangladesh-record
bangladesh-record:
	$(PYTHON) -m src.compute.bangladesh_record
validate-bangladesh-record:
	$(PYTHON) -m src.compute.validate_bangladesh_record
