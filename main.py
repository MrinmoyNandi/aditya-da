import os
from typing import Any

import requests
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(system|user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = Field(default_factory=list)
    allow_fallback: bool = False
    force_provider: str | None = None


class ChatResponse(BaseModel):
    reply: str | None = None
    provider: str | None = None
    requires_confirmation: bool = False
    confirmation_message: str | None = None
    available_cloud_providers: list[str] = Field(default_factory=list)
    error: str | None = None


app = FastAPI(title="Aditya DA Chatbot")


FRONTEND_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Aditya DA Chatbot</title>
    <script crossorigin src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script crossorigin src="https://unpkg.com/@mui/material@5/umd/material-ui.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <style>
      html, body, #root { margin: 0; padding: 0; width: 100%; height: 100%; }
    </style>
  </head>
  <body>
    <div id="root"></div>
    <script type="text/babel">
      const {
        ThemeProvider, createTheme, CssBaseline, AppBar, Toolbar, Typography, IconButton,
        Box, Paper, TextField, Button, Stack, Chip, Divider, CircularProgress, Alert
      } = MaterialUI;
      const { useMemo, useState } = React;

      function App() {
        const [mode, setMode] = useState(localStorage.getItem("themeMode") || "light");
        const [input, setInput] = useState("");
        const [messages, setMessages] = useState([]);
        const [loading, setLoading] = useState(false);
        const [provider, setProvider] = useState("not selected");
        const [pendingConfirmation, setPendingConfirmation] = useState(null);
        const [error, setError] = useState("");

        const theme = useMemo(() => createTheme({ palette: { mode } }), [mode]);

        const conversationHistory = messages.map((m) => ({
          role: m.role === "bot" ? "assistant" : "user",
          content: m.text
        }));

        const sendMessage = async (allowFallback = false) => {
          if (!input.trim()) return;
          const userText = input.trim();
          setInput("");
          setError("");
          setMessages((prev) => [...prev, { role: "user", text: userText }]);
          setLoading(true);
          try {
            const res = await fetch("/api/chat", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                message: userText,
                history: conversationHistory,
                allow_fallback: allowFallback
              })
            });
            const data = await res.json();
            if (!res.ok || data.error) {
              throw new Error(data.error || "Request failed.");
            }
            if (data.requires_confirmation) {
              setPendingConfirmation({
                text: data.confirmation_message || "Fallback needed.",
                providers: data.available_cloud_providers || []
              });
              setMessages((prev) => [...prev, { role: "bot", text: data.confirmation_message || "Fallback required before continuing." }]);
            } else if (data.reply) {
              setProvider(data.provider || "unknown");
              setPendingConfirmation(null);
              setMessages((prev) => [...prev, { role: "bot", text: data.reply }]);
            }
          } catch (e) {
            setError(e.message || "Unexpected error.");
          } finally {
            setLoading(false);
          }
        };

        const handleConfirmFallback = async (accept) => {
          if (!accept) {
            setPendingConfirmation(null);
            setMessages((prev) => [...prev, { role: "bot", text: "Okay, fallback canceled. Please configure a local model in Ollama or choose another setup." }]);
            return;
          }
          if (!messages.length) return;
          const lastUser = [...messages].reverse().find((m) => m.role === "user");
          if (!lastUser) return;
          setInput(lastUser.text);
          await sendMessage(true);
        };

        return (
          <ThemeProvider theme={theme}>
            <CssBaseline />
            <Box sx={{ display: "flex", flexDirection: "column", height: "100%" }}>
              <AppBar position="static">
                <Toolbar>
                  <Typography variant="h6" sx={{ flexGrow: 1 }}>Aditya DA Chatbot</Typography>
                  <Chip label={`Provider: ${provider}`} color="secondary" sx={{ mr: 2 }} />
                  <IconButton
                    color="inherit"
                    onClick={() => {
                      const next = mode === "light" ? "dark" : "light";
                      setMode(next);
                      localStorage.setItem("themeMode", next);
                    }}
                  >
                    {mode === "light" ? "🌙" : "☀️"}
                  </IconButton>
                </Toolbar>
              </AppBar>

              <Box sx={{ flex: 1, p: { xs: 1, sm: 2 }, overflow: "auto" }}>
                <Stack spacing={1.5}>
                  {messages.map((m, i) => (
                    <Paper
                      key={i}
                      elevation={2}
                      sx={{
                        p: 1.5,
                        alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                        maxWidth: { xs: "92%", sm: "75%" },
                        bgcolor: m.role === "user" ? "primary.main" : "background.paper",
                        color: m.role === "user" ? "primary.contrastText" : "text.primary",
                        borderRadius: 2
                      }}
                    >
                      <Typography variant="body1">{m.text}</Typography>
                    </Paper>
                  ))}
                  {loading && <CircularProgress size={24} />}
                </Stack>
              </Box>

              <Divider />
              <Box sx={{ p: { xs: 1, sm: 2 } }}>
                {error && <Alert severity="error" sx={{ mb: 1 }}>{error}</Alert>}
                {pendingConfirmation && (
                  <Alert severity="warning" sx={{ mb: 1 }}>
                    <Typography variant="body2" sx={{ mb: 1 }}>{pendingConfirmation.text}</Typography>
                    {pendingConfirmation.providers.length > 0 && (
                      <Typography variant="caption" display="block" sx={{ mb: 1 }}>
                        Available cloud providers: {pendingConfirmation.providers.join(", ")}
                      </Typography>
                    )}
                    <Stack direction="row" spacing={1}>
                      <Button variant="contained" size="small" onClick={() => handleConfirmFallback(true)}>Use API key fallback</Button>
                      <Button variant="outlined" size="small" onClick={() => handleConfirmFallback(false)}>Cancel</Button>
                    </Stack>
                  </Alert>
                )}
                <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
                  <TextField
                    fullWidth
                    label="Type your message"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        if (!loading) sendMessage(false);
                      }
                    }}
                  />
                  <Button variant="contained" disabled={loading} onClick={() => sendMessage(false)}>Send</Button>
                </Stack>
              </Box>
            </Box>
          </ThemeProvider>
        );
      }

      ReactDOM.createRoot(document.getElementById("root")).render(<App />);
    </script>
  </body>
</html>
"""


def app_mode() -> str:
    mode = os.getenv("APP_MODE", "").strip().lower()
    if mode in {"local", "deployed"}:
        return mode
    if os.getenv("DEPLOYED", "").strip().lower() in {"1", "true", "yes"}:
        return "deployed"
    return "local"


def cloud_providers_in_priority() -> list[str]:
    providers: list[str] = []
    if os.getenv("GEMINI_API_KEY"):
        providers.append("gemini")
    if os.getenv("OPENAI_API_KEY"):
        providers.append("openai")
    if os.getenv("GROQ_API_KEY"):
        providers.append("groq")
    return providers


def build_messages(history: list[ChatMessage], user_message: str) -> list[dict[str, str]]:
    messages = [{"role": "system", "content": "You are a helpful, concise assistant."}]
    messages.extend({"role": item.role, "content": item.content} for item in history)
    messages.append({"role": "user", "content": user_message})
    return messages


def ollama_model_available() -> bool:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "llama3")
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json().get("models", [])
        return any(item.get("name", "").split(":")[0] == model.split(":")[0] for item in models)
    except requests.RequestException:
        return False


def call_ollama(messages: list[dict[str, str]]) -> str:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "llama3")
    response = requests.post(
        f"{base_url}/api/chat",
        json={"model": model, "messages": messages, "stream": False},
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["message"]["content"]


def call_gemini(messages: list[dict[str, str]]) -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    prompt = "\n".join(f'{m["role"]}: {m["content"]}' for m in messages)
    response = requests.post(
        url,
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def call_openai(messages: list[dict[str, str]]) -> str:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": model, "messages": messages},
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def call_groq(messages: list[dict[str, str]]) -> str:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not configured.")
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": model, "messages": messages},
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def run_provider(provider: str, messages: list[dict[str, str]]) -> str:
    if provider == "ollama":
        return call_ollama(messages)
    if provider == "gemini":
        return call_gemini(messages)
    if provider == "openai":
        return call_openai(messages)
    if provider == "groq":
        return call_groq(messages)
    raise RuntimeError(f"Unknown provider: {provider}")


def pick_provider(payload: ChatRequest) -> tuple[str | None, ChatResponse | None]:
    mode = app_mode()
    cloud = cloud_providers_in_priority()
    local_available = ollama_model_available()

    if payload.force_provider:
        chosen = payload.force_provider.lower()
        if chosen == "ollama" and not local_available:
            return None, ChatResponse(error="Requested provider 'ollama' is unavailable or model is missing.")
        if chosen in {"gemini", "openai", "groq"} and chosen not in cloud:
            return None, ChatResponse(error=f"Requested provider '{chosen}' is not configured.")
        return chosen, None

    if mode == "local":
        if local_available:
            return "ollama", None
        if cloud:
            if payload.allow_fallback:
                return cloud[0], None
            return None, ChatResponse(
                requires_confirmation=True,
                confirmation_message=(
                    "Local Ollama model is unavailable. Do you want to switch to API-key providers for this chat?"
                ),
                available_cloud_providers=cloud,
            )
        return None, ChatResponse(
            error=(
                "No local Ollama model is available and no cloud API keys are configured. "
                "Configure Ollama model or set GEMINI_API_KEY / OPENAI_API_KEY / GROQ_API_KEY."
            )
        )

    if cloud:
        return cloud[0], None
    if local_available:
        return "ollama", None
    return None, ChatResponse(
        error=(
            "Deployed mode is active, but no cloud API keys are configured and local Ollama is unavailable. "
            "Set GEMINI_API_KEY, OPENAI_API_KEY, or GROQ_API_KEY."
        )
    )


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return FRONTEND_HTML


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    selected_provider, early_response = pick_provider(payload)
    if early_response:
        return early_response
    if not selected_provider:
        return ChatResponse(error="No provider selected.")

    messages = build_messages(payload.history, payload.message)
    try:
        reply = run_provider(selected_provider, messages)
    except requests.RequestException as exc:
        return ChatResponse(error=f"{selected_provider} request failed: {exc}")
    except (KeyError, IndexError, TypeError, RuntimeError) as exc:
        return ChatResponse(error=f"{selected_provider} response error: {exc}")
    return ChatResponse(reply=reply, provider=selected_provider)

