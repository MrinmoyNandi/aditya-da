# Aditya DA Chatbot

A responsive chatbot with:
- **Material UI frontend** (React + MUI via CDN)
- **Light/Dark mode toggle**
- **Mobile-friendly layout**
- **Provider routing logic** for local and deployed environments

## Provider Behavior

This app supports:
- **Ollama** (local)
- **Gemini**
- **OpenAI GPT**
- **Groq**

### Local mode (`APP_MODE=local`, default)
1. Try **Ollama** first.
2. If local model is missing/unavailable:
   - If API keys exist, app **asks user** whether to fallback to cloud providers.
   - If user accepts, app uses priority: `Gemini -> OpenAI -> Groq`.
3. If no fallback provider is configured, returns setup error.

### Deployed mode (`APP_MODE=deployed` or `DEPLOYED=true`)
1. Use cloud providers in priority: `Gemini -> OpenAI -> Groq`.
2. If no cloud API keys are configured, it can still use Ollama only if available.
3. Otherwise returns configuration error.

## Environment Variables

### App mode
- `APP_MODE=local|deployed` (optional, defaults to `local`)
- `DEPLOYED=true` (optional shortcut for deployed mode when `APP_MODE` is unset)

### Ollama
- `OLLAMA_BASE_URL` (default: `http://127.0.0.1:11434`)
- `OLLAMA_MODEL` (default: `llama3`)

### Gemini
- `GEMINI_API_KEY`
- `GEMINI_MODEL` (default: `gemini-1.5-flash`)

### OpenAI GPT
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (default: `gpt-4o-mini`)

### Groq
- `GROQ_API_KEY`
- `GROQ_MODEL` (default: `llama-3.1-8b-instant`)

## Local Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open: `http://127.0.0.1:8000`

## Deploy Notes

Set `APP_MODE=deployed` and configure at least one key:
- `GEMINI_API_KEY` or
- `OPENAI_API_KEY` or
- `GROQ_API_KEY`

Recommended for production:
- Keep secrets in platform secret manager.
- Use HTTPS.
- Restrict CORS as needed behind your deployment stack.

## UI Features

- Material UI app shell
- Responsive chat layout for desktop/mobile
- Chat bubbles for user/assistant
- Loading indicator
- Error alerts
- Light/Dark theme switch (persisted in browser storage)
