# ECOnexão Backend

API de domínio FastAPI da ECOnexão. O backend expõe os endpoints sob
`/api/v1`; migrations e políticas de banco permanecem exclusivamente em
`../supabase/migrations`.

## Desenvolvimento local

Requer Python 3.13.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Smoke checks:

- `GET http://127.0.0.1:8000/api/v1/health/live`
- `GET http://127.0.0.1:8000/docs`

Qualidade:

```powershell
python -m pytest
python -m ruff check .
python -m mypy app
```

O endpoint de liveness não depende de banco. O readiness só poderá ser
considerado operacional após a conexão Supabase ser implementada e verificada
na task correspondente.
