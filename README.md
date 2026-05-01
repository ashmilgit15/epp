# E++ (e-plus-plus)

E++ is a beginner-friendly, English-like programming language with a built-in Python-based interpreter, natively integrated desktop GUI syntax, and a dedicated Electron-based IDE featuring an AI coding assistant.

## Features

- **English-like Syntax:** Designed for complete beginners. No brackets—just indentation and colons. (e.g., `if x is greater than 10:`)
- **Native GUI Framework:** Build desktop applications with zero boilerplate using built-in keywords like `window`, `label`, `button`, and `input`.
- **Standard Library:** Includes common utilities, math functions, JSON parsing, file I/O, and native `fetch` for networking.
- **Dedicated IDE:** A standalone Electron + Monaco IDE with syntax highlighting, an integrated terminal, and a one-click execution environment.
- **Built-in AI Agent:** The IDE ships with a Cursor-style AI Agent powered by Llama 3.1 70B/405B that can auto-stream code directly into your editor buffer.

## Getting Started

### Language Example

```epp
# A simple GUI application in E++
window "Welcome" width 400 height 300 color "black"

label "Welcome to our App" at 20 20 font_size 24 color "white"
button "Proceed" at 20 100 width 200 height 30 color "darkgray" on_click proceed_func

func proceed_func():
    alert "Welcome! You can now use our app."

show_window
```

### Running E++ Code

You can use the bundled standalone interpreter:
```bash
./dist/epp my_script.epp
```

Or just open the file in the E++ IDE and click **Run (F5)**!
