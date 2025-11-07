# Backend FastAPI

API responsável por orquestrar trabalhos de audiodescrição. Expõe endpoints para criação de jobs, acompanhamento de progresso e download de artefatos.

## Executando localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn ad_webapi.main:app --reload
```
