# syntax=docker/dockerfile:1
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml README.md /app/
COPY ad_webapi /app/ad_webapi
RUN pip install --upgrade pip && pip install .
EXPOSE 8000
CMD ["uvicorn", "ad_webapi.main:app", "--host", "0.0.0.0", "--port", "8000"]
