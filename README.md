# Property Management Email Assistant

**An AI‑powered FastAPI service that triages property‑management e‑mails, generates LLM replies, and turns actionable items into support tickets – all through a clean JSON/REST interface.**


---

## ✨ Key Features

* **E‑mail ingestion** – fetch unread or recent messages directly from Gmail via the `/workflows/fetch-gmail` endpoint.
* **AI response generation** – LangChain + OpenAI / Anthropic / Ollama models propose multiple reply options, stored in a *waiting zone* for human review.
* **Action‑item extraction** – converts bullet‑point action items in the e‑mail body into structured JSON.
* **Ticket creation** – pushes selected action items into the internal ticket system (`/tickets/*`).
* **Workflow API** – single endpoint (`POST /workflows/process-emails`) triggers the full pipeline from fetch → AI reply → ticket.
* **Health & analytics** – built‑in `/health` and `/emails/analytics/summary` endpoints plus TinyDB/SQLAlchemy stats.
* **Pluggable vector search** – optional FAISS + sentence‑transformers for semantic look‑ups.
* **Async & background tasks** – APScheduler + Celery + Redis keep long‑running jobs out of the request loop.

---

## 🏗️ Tech‑Stack

| Layer                 | Details                                                        |
| --------------------- | -------------------------------------------------------------- |
| **API**               | FastAPI (uvicorn hot‑reload)                                   |
| **LLM**               | LangChain wrappers for OpenAI, Anthropic, Ollama, Hugging Face |
| **Persistence**       | TinyDB (default dev DB) • PostgreSQL (via SQLAlchemy)          |
| **Queue / Scheduler** | Celery • Redis • APScheduler                                   |
| **Vector Store**      | FAISS‑CPU                                                      |
| **Testing & Tooling** | (TBD) pytest, ruff, black,                                     |

---

## ⚡ Quick Start

> **TL;DR** – three commands and you’re in the docs at [http://localhost:8000/docs](http://localhost:8000/docs).

```bash
# 1. Clone & enter
git clone https://github.com/jsrobin888/property-assistant-app.git
cd property-assistant-app

# 2. Python env & deps  (≈30 s with uv)
uv venv           # creates .venv
uv pip install -r requirements.txt
cp .env.local.copy .env.local   # fill in API keys: OPENAI_API_KEY, GMAIL_* …

# 3. Run the API
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

**FYI: Wait until shows "INFO:     Application startup complete."
```

The interactive swagger UI will be available at [http://localhost:8000/docs](http://localhost:8000/docs) and ReDoc at `/redoc`.

### One‑line sanity check

```bash
python -c "import langchain_openai, numpy, fastapi, torch; print('✅ env looks good')"
```

---

## 🔌 Environment Variables

| Variable                                  | What for        | Example                                   |
| ----------------------------------------- | --------------- | ----------------------------------------- |
| `OPENAI_API_KEY`                          | LLM replies     | `sk‑…`                                    |
| `ANTHROPIC_API_KEY`                       | optional        |                                           |
| `DATABASE_URL`                            | Postgres (prod) | `postgresql+psycopg2://user:pass@host/db` |
| `REDIS_URL`                               | optional        | `redis://localhost:6379/0`                |
| `GMAIL_IMAP_HOST`, `GMAIL_USERNAME`, `GMAIL_PASSWORD`       | IMAP/GMAIL auth |   |
| `SCHEDULER_MODE`                          | CRON Scheduler  | |
| `USE_LOCAL_MODELS`                        | LLM Ollama      | boolean `true` or `false` |
| `LOCAL_AI_BASE_URL`                      | LLM Ollama      | `http://0.0.0.0:11434`    |
| `LOG_LEVEL`                               | logging         |   |
| `LOADER_VERIFICATION`                     | logging         |   |
For local hacking you can leave **DATABASE\_URL** empty to fall back to in‑memory TinyDB.

---

## 🛰️ API Cheatsheet

| Endpoint                              | Verb   | Description                                  |
| ------------------------------------- | ------ | -------------------------------------------- |
| `/api/v1/workflows/process-emails`    | `POST` | Run full ingest → AI → ticket pipeline       |
| `/api/v1/workflows/fetch-gmail`       | `POST` | Pull unread / recent / count‑limited e‑mails |
| `/api/v1/workflows/status/{{id}}`     | `GET`  | Check background‑workflow progress           |
| `/api/v1/emails/ai-responses/pending` | `GET`  | List AI replies awaiting approval            |
| `/api/v1/tickets/`                    | `GET`  | Filter & search tickets                      |
| `/health`                             | `GET`  | Service heartbeat                            |

*(see `app/api/routes.py` for the full list)*

---

## 🐳 Docker (optional)

```bash
[Optional] docker-compose down -v 
docker-compose up --build
```

---

## 🧪 Quick Tests (optional)

```bash
python -c "import langchain_openai; print('✅ LangChain OpenAI installed')"
python -c "import langchain_huggingface; print('✅ LangChain HuggingFace installed')"
python -c "import sentence_transformers; print('✅ Sentence Transformers installed')"
python -c "import numpy; print(f'✅ NumPy {numpy.__version__}')"
python -m app.examples.use_cases.integration_cases full
```


---

## 🤝 Contributing

1. Fork → feature branch → PR
2. Ensure `pytest`, `ruff`, and `black` pass
3. Document new endpoints in **README** and `/docs`

---

## 📜 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

---

> *Happy automating property management!*
