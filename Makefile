.PHONY: install download data train evaluate pipeline test lint api ui \
        docker-build docker-up docker-down clean

install:        ## Install runtime + dev dependencies
	pip install -r requirements-dev.txt

download:       ## Download optional OWID covariates into data/raw/
	python -m src.data.download_data

data:           ## Build the processed dataset
	python -m src.data.process_data

train:          ## Train the models
	python -m src.model.train

evaluate:       ## Evaluate on the held-out test set
	python -m src.model.evaluate

pipeline: data train evaluate  ## Run the full data + model pipeline

test:           ## Run the test suite
	python -m pytest -q

api:            ## Run the API locally (port 8000)
	uvicorn src.api.main:app --reload --port 8000

ui:             ## Run the Streamlit UI locally (port 8501)
	streamlit run src/ui/app.py

docker-build:   ## Build the Docker image
	docker compose build

docker-up:      ## Build and run API + UI via Docker (UI on :8501)
	docker compose up --build

docker-down:    ## Stop the Docker stack
	docker compose down

clean:          ## Remove generated data + model artifacts
	rm -rf data/processed/* models/*.pkl models/*.json
