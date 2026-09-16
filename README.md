# Gap Field — Backend (FastAPI)

A minimal backend that takes a prompt from your frontend and forwards it to Claude, keeping your `ANTHROPIC_API_KEY` on the server. Deployable on Railway, Render, or Heroku.

## What was fixed from the original file

Your uploaded `main.py` (extracted from a PDF) had broken syntax that would fail immediately on `uvicorn main:app`:

- `from fastapi.middleware.cors import\nCORSMiddleware` — the import was split across a line break, so Python saw an incomplete `import` statement.
- `@app.post("/analyze")async def analyze(...)` — no line break between the decorator and the function definition, which is a syntax error.
- No error handling — a failed or slow Anthropic call, or a missing API key, would crash the request with an unhandled exception instead of a clean error message.
- `allow_origins=["*"]` combined with wide-open CORS is fine for testing but not something you want left on for a real deployment.

This version fixes all of the above, adds `/health`, input validation via Pydantic, and pinned dependency versions so the build is reproducible.

## Project structure

```
gap-field-py/
├── main.py          # FastAPI app
├── requirements.txt # pinned dependencies
├── runtime.txt       # Python version pin
├── Procfile          # process command for Railway/Render/Heroku
├── .env.example
└── .gitignore
```

## Run locally

Requires Python 3.11+.

```bash
git clone https://github.com/<your-username>/gap-field-py.git
cd gap-field-py
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then put your real key in .env
export $(cat .env | xargs)      # or use a tool like python-dotenv / honcho
uvicorn main:app --reload
```

Open http://localhost:8000 — you should see `{"status": "Gap Field backend is running"}`.

Test the endpoint:

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Say hello in one sentence."}'
```

## Deploy

### Railway / Render

1. Push this folder to a GitHub repo.
2. Create a new **Web Service** and connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: leave blank if the platform reads the `Procfile` automatically (Railway does); otherwise set it to `uvicorn main:app --host 0.0.0.0 --port $PORT`.
5. Add environment variables: `ANTHROPIC_API_KEY` (required), `ALLOWED_ORIGINS` (your frontend's URL — do not leave this as `*` in production).
6. Deploy.

### Heroku

```bash
heroku create
heroku buildpacks:set heroku/python
git push heroku main
heroku config:set ANTHROPIC_API_KEY=sk-ant-...
heroku config:set ALLOWED_ORIGINS=https://your-frontend.com
```

The `Procfile` tells all three platforms how to start the app.

## Environment variables

| Name | Required | Default | Purpose |
| --- | --- | --- | --- |
| `ANTHROPIC_API_KEY` | yes | — | Your Anthropic API key |
| `ANTHROPIC_MODEL` | no | `claude-sonnet-5` | Model used for the request |
| `ALLOWED_ORIGINS` | no | `*` | Comma-separated frontend origins allowed to call this API |
| `PORT` | set by platform | `8000` locally | Port the server listens on |

## API

`POST /analyze`

```json
{ "prompt": "your prompt text here" }
```

Response:

```json
{ "text": "model's reply" }
```

Errors return `{ "detail": "message" }` with a 4xx/5xx status instead of crashing.

## License

MIT.
