# E++ (e-plus-plus) v2.1

E++ is a beginner-friendly, English-like programming language with a built-in Python-based interpreter, natively integrated desktop GUI syntax, canvas drawing & animation, and a dedicated Electron-based IDE featuring an AI coding assistant.

## Features

- **English-like Syntax:** Designed for complete beginners. No brackets — just indentation and colons. (e.g. `if x is greater than 10:` — and yes, `if x > 10:` works too)
- **String Interpolation:** `say "Hello {name}, you have {coins * 2} coins!"` — with Python-style format specs: `"total: {price:,.2f}"`

- **Membership tests:** `if "apple" in fruits:` / `if user not in banned:`
- **Native GUI Framework:** Build desktop apps with zero boilerplate: `window`, `label`, `button`, `input`, `slider`, `progress`, `dropdown`, `checkbox`, `textbox`, `image`
- **Canvas & Animation:** `canvas` + `draw circle on "cv" at 100 100 size 40 color "red"` + `every 50 milliseconds call tick` — games and art made simple
- **Modern Language Core:** indexing (`items[0]`, `items[-1]`, chained), dicts, classes with method arguments, `try/catch`, `switch`, `repeat N times:`, `break`/`continue`, compound assignment (`+=`)
- **Standard Library:** 50+ built-ins including JSON, files, math, randomness, and native `fetch`/`fetch_json` for networking
- **Friendly Errors:** Line **and column** numbers + plain-English suggestions ("Did you forget to assign it?") — plus `--check`, `--tokens` and `--ast` CLI tools

- **CI & Tooling:** GitHub Actions test matrix, live error squiggles in the IDE, one-command PyInstaller build (`scripts/build_binary.sh`)
- **Dedicated IDE:** Electron + Monaco IDE with autocomplete, hover docs, error-line highlighting, examples gallery, themes and resizable panels
- **Built-in AI Agent:** Bring your own key (any OpenAI-compatible provider — Nvidia NIM, OpenAI, Groq, Ollama...) and get streaming E++ code straight into the editor

## Getting Started

### Language Example

```epp
# A tiny GUI app in E++
window "Welcome" width 400 height 300 color "black"

label "Welcome to our App" at 20 20 font_size 24 color "white"
button "Proceed" at 20 100 width 200 height 30 color "darkgray" on_click proceed_func

func proceed_func():
    alert "Welcome! You can now use our app."

show_window
```

### Canvas example (new in v2)

```epp
window "Starfield" width 500 height 400 color "black"
canvas "cv" width 480 height 360 color "black"

every 100 milliseconds call twinkle

func twinkle():
    draw dot on "cv" at random_int(0, 480) random_int(0, 360) color "white"

show_window
```

### Running E++ Code

With Python (no build step needed):
```bash
python3 -m interpreter.epp my_script.epp      # run a file
python3 -m interpreter.epp                    # interactive REPL
python3 -m interpreter.epp -e 'say 2 ^ 10'    # one-liner
```

Or open the file in the E++ IDE and click **Run (F5)**.

```bash
cd epp-ide && npm install && npm start
```

Build a standalone binary (optional):
```bash
pip install pyinstaller
./scripts/build_binary.sh     # produces dist/epp
```

### Running the tests

```bash
python3 -m unittest discover -s tests -v
```

CI runs the suite on every push (Python 3.10–3.13, IDE syntax checks, and a secret scanner).

## Documentation

- [LANGUAGE_SPEC.md](LANGUAGE_SPEC.md) — full language reference
- [GETTING_STARTED.md](GETTING_STARTED.md) — beginner tutorial
- [grammar.ebnf](grammar.ebnf) — formal grammar
- [tests/examples/](tests/examples/) — runnable sample programs
- [epp-ide/README.md](epp-ide/README.md) — IDE details & AI setup

## Security note

Previous versions shipped an AI API key in source control — **revoke that key**. The AI agent now reads configuration from the environment (`EPP_AI_API_KEY`, `EPP_AI_BASE_URL`, `EPP_AI_MODEL`) or from `epp-ide/config.json` (gitignored; see `config.json.example`).
