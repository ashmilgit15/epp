# E++ IDE

The official IDE for the e++ programming language.

## Features

- **Syntax Highlighting**: Full e++ language support with Monaco Editor
- **Autocomplete & Hover Docs**: `Ctrl+Space` for every keyword, stdlib function and snippet; hover any function for its signature
- **Live Error Squiggles**: The interpreter checks your file as you type (parse-only `--check` mode) and underlines problems with messages — before you even run
- **File Explorer**: Create, edit, delete, and rename files
- **Run & Debug**: Execute e++ programs with output panel — runtime errors automatically highlight the offending line
- **Examples Gallery**: One-click runnable sample programs (games, GUI apps, canvas art, timers)
- **Themes**: Light/dark toggle (remembered between sessions)
- **Resizable Panels**: Drag to resize explorer, terminal and AI sidebar
- **Keyboard Shortcuts**:
  - `Ctrl+S` — Save
  - `F5` / `Ctrl+Enter` — Run
  - `Ctrl+N` — New file
  - `Escape` — Close dialogs

## Running in Development

```bash
npm install
npm start
```

The IDE runs `.epp` files with the bundled interpreter binary if present (`dist/epp`), otherwise it falls back to `python3 -m interpreter.epp` from the repo root — no packaging required.

## AI Agent Setup (Bring Your Own Key)

The built-in AI agent works with **any OpenAI-compatible chat completions API**.
The defaults are wired for **Hack Club AI** (`https://ai.hackclub.com/proxy/v1`, model `stealth/ox-alpha`).

**Hack Club (recommended):**
```bash
cp config.json.example config.json   # then paste your sk-hc-... key into config.json
npm start
```
Or via env vars:
```bash
export EPP_AI_API_KEY="sk-hc-v1-..."
export EPP_AI_BASE_URL="https://ai.hackclub.com/proxy/v1"
export EPP_AI_MODEL="stealth/ox-alpha"
npm start
```

**Other providers** (env vars or config.json):
```bash
export EPP_AI_API_KEY="nvapi-... or sk-... or gsk_..."
export EPP_AI_BASE_URL="https://integrate.api.nvidia.com/v1"   # Nvidia example
export EPP_AI_MODEL="meta/llama-3.1-405b-instruct"
```

Supported providers include Hack Club AI, Nvidia NIM, OpenAI, Groq, Together, OpenRouter and local [Ollama](https://ollama.com) (`http://localhost:11434/v1`). The agent automatically sends your current editor content for context, caps history, and shows a **Stop** button while generating; chips like **Explain / Fix bugs / Tests / Game** let you prompt in one click.

> **Security:** never commit API keys. Older versions of this project shipped a key in source control — it has been removed; revoke it if you had enabled it.

## Building for Production

```bash
# Windows
npm run build:win

# Linux
npm run build:linux

# macOS
npm run build:mac
```

## Requirements

- Node.js 18+
- Either a bundled interpreter binary at `../dist/epp` **or** Python 3.10+ on PATH
