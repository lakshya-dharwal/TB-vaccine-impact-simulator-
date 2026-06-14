# TB Futures — single image that serves either the API or the Streamlit UI.
# The dataset and model are built into the image at build time from the tracked
# raw data, so the container starts ready to serve.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build the processed dataset and train the model into the image.
RUN python -m src.data.process_data && python -m src.model.train

EXPOSE 8000 8501

# Default: the API. The UI service overrides this command (see docker-compose.yml
# / render.yaml).
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
