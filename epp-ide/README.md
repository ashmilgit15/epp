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

Configure via environment variables:

```bash
export EPP_AI_API_KEY="nvapi-... or sk-... or gsk_..."
export EPP_AI_BASE_URL="https://integrate.api.nvidia.com/v1"   # optional
export EPP_AI_MODEL="meta/llama-3.1-405b-instruct"             # optional
npm start
```

...or copy `config.json.example` to `config.json` and fill in your values (this file is gitignored).

Supported providers include Nvidia NIM, OpenAI, Groq, Together, OpenRouter and local [Ollama](https://ollama.com) (`http://localhost:11434/v1`).

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
