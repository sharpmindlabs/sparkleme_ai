# SparkleMe dev convenience targets
ENGINE=services/inference_engine

.PHONY: install fixtures test engine web demo

install:
	cd $(ENGINE) && pip install -r requirements.txt

fixtures:            ## generate placeholder client images so mock runs
	cd $(ENGINE) && python scripts/make_fixtures.py 6

test:
	cd $(ENGINE) && python -m pytest tests/ -q

engine:              ## serve the inference API on :8000
	cd $(ENGINE) && uvicorn app.api:app --reload --port 8000

web:                 ## serve the review UI (needs `npm install` first)
	cd apps/web && npm run dev

demo:                ## fixtures + a mock batch from the CLI
	cd $(ENGINE) && python scripts/make_fixtures.py 6 && SPARKLEME_PROVIDER=mock python -m app.cli
