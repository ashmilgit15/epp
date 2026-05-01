# E++ IDE

The official IDE for the e++ programming language.

## Features

- **Syntax Highlighting**: Full e++ language support with Monaco Editor
- **File Explorer**: Create, edit, delete, and rename .epp files
- **Run & Debug**: Execute e++ programs with output panel
- **Auto-indentation**: Automatic indentation for Python-like syntax
- **Dark Theme**: Easy on the eyes dark mode
- **Keyboard Shortcuts**: 
  - `Ctrl+S` - Save
  - `F5` - Run
  - `Ctrl+N` - New file (from toolbar)

## Running in Development

```bash
npm install
npm start
```

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
- The epp interpreter (bundled automatically)