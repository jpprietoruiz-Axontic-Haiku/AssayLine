# AssayLine

Pipeline agéntico que convierte informes técnicos industriales/de laboratorio
desordenados (PDF, escaneos, fotos, tablas mal formadas) en datos estructurados y
validados, marca anomalías fuera de especificación, y permite revisión
human-in-the-loop antes de exportar.

> Estado: en construcción — ver hitos abajo. Datos de demo 100% sintéticos.

## Arquitectura

```
Upload -> job en cola (Redis + RQ) -> worker:
  1. clasifica tipo de informe
  2. OCR/visión sobre páginas e imágenes (incluye gráficas)
  3. agente con tool-calling: extrae campos, llama a herramientas
     (conversión de unidades, lookup de spec_profiles, cálculo)
  4. valida contra esquema Pydantic; lo que no valida, se marca
  5. compara valores vs spec_profiles -> flags de anomalía
-> resultado a Postgres -> dashboard: revisión human-in-the-loop -> export
```

Diagrama Mermaid detallado y decisiones de diseño: ver `DECISIONS.md` (hito 6).

## Stack

- **Worker**: Python + FastAPI, agente con tool-calling (Anthropic tool use),
  visión multimodal, validación con Pydantic.
- **Cola de jobs**: Redis + RQ.
- **Dashboard**: React + Vite + TypeScript.
- **Datos**: Postgres (`reports`, `extractions`, `anomalies`, `reviews`, `spec_profiles`).
- **Deploy**: Railway (worker + Postgres + Redis) + Vercel (dashboard).

## Estructura del monorepo

```
worker/     FastAPI + agente de extracción + tests (pytest)
dashboard/  React + Vite + TypeScript
infra/      docker-compose (Postgres+Redis) + migraciones SQL
```

## Desarrollo local

```bash
cp .env.example .env          # y worker/.env / dashboard/.env según haga falta
docker compose -f infra/docker-compose.yml up -d   # Postgres + Redis

cd worker
python -m venv .venv && .venv/Scripts/activate     # o source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload

cd ../dashboard
npm install
npm run dev
```

## Tests y lint

```bash
cd worker && pytest -q && ruff check .
cd dashboard && npm run build   # incluye typecheck (tsc -b)
```

## Hitos

1. [x] Scaffolding monorepo + schema Postgres + docker-compose + CI
2. [ ] Ingesta: `POST /reports` + clasificación + OCR/visión
3. [ ] Agente de extracción con tool-calling + validación Pydantic
4. [ ] Motor de anomalías + informes sintéticos de demo
5. [ ] Dashboard de revisión (lado a lado, edición inline, export)
6. [ ] README senior + diagrama Mermaid + `DECISIONS.md`
