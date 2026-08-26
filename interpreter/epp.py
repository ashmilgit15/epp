#!/usr/bin/env python3
"""E++ interpreter command-line interface.

Usage:
    python3 -m interpreter.epp <file.epp>     run a program
    python3 -m interpreter.epp -e "<code>"    evaluate a one-liner
    python3 -m interpreter.epp                start the interactive REPL
"""
import sys
import os

# Allow running both as `python3 -m interpreter.epp` and `python3 interpreter/epp.py`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interpreter.lexer import Lexer
from interpreter.parser import Parser
from interpreter.evaluator import Evaluator
from interpreter.stdlib import make_stdlib
from interpreter.errors import EppError

BANNER = r"""
  ███████╗    ██╗  ██╗     ██████╗
  ██╔════╝    ██║  ██║    ╚════██╗
  █████╗      ███████║      █████╔╝
  ██╔══╝      ██╔══██║     ██╔═══╝
  ███████╗    ██║  ██║    ███████╗
  ╚══════╝    ╚═╝  ╚═╝    ╚══════╝
  E++ — the English-like programming language
  Type your code, or 'help' for help, 'exit' to quit.
"""

HELP_TEXT = """
REPL commands:
  help              show this message
  exit / quit       leave the REPL
  vars              list defined variables
  clear             clear the screen

Everything else is E++ code! Try:
  say "Hello {1 + 1}"
  repeat 3 times:
      say "echo"
"""


def create_evaluator(script_dir=None):
    evaluator = Evaluator()
    stdlib = make_stdlib(evaluator)
    evaluator.register_stdlib(stdlib)
    if script_dir:
        evaluator.script_dir = script_dir
    return evaluator


def run_source(source, evaluator):
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse()
    return evaluator.eval(program)


def _supports_color():
    return sys.stdout.isatty() and os.environ.get('NO_COLOR') is None


def _fail(message):
    if _supports_color():
        print(f"\033[1;31m{message}\033[0m", file=sys.stderr)
    else:
        print(message, file=sys.stderr)
    sys.exit(1)


def check_file(filepath, as_json=False):
    """Parse-only mode used by tools/IDE for live error reporting."""
    with open(filepath, 'r') as f:
        source = f.read()
    try:
        tokens = Lexer(source).tokenize()
        Parser(tokens).parse()
        if as_json:
            print('{"ok": true}')
        else:
            print("No issues found.")
        return 0
    except EppError as e:
        line = e.line if e.line is not None else -1
        column = e.column if e.column is not None else -1
        message = str(e.args[0]) if e.args else str(e)
        suggestion = getattr(e, 'suggestion', None) or ''
        if as_json:
            import json
            print(json.dumps({
                "ok": False,
                "errors": [{
                    "line": line,
                    "column": column,
                    "message": message,
                    "suggestion": suggestion,
                }]
            }))
        else:
            print(str(e))
        return 1


def dump_tokens(source):
    tokens = Lexer(source).tokenize()
    for t in tokens:
        value = repr(t.value) if t.value is not None else ''
        print(f"  {t.line:>4}:{t.column:<3} {t.type:<14} {value}")


def dump_ast(source):
    program = Parser(Lexer(source).tokenize()).parse()

    def walk(node, depth=0):
        name = type(node).__name__
        pad = '  ' * depth
        extra = ''
        if isinstance(node, (Number, String, Boolean)):
            extra = f' {node.value!r}'
        elif isinstance(node, Identifier):
            extra = f' {node.name}'
        print(f"{pad}{name}{extra}")
        for key, value in vars(node).items() if hasattr(node, '__dict__') else []:
            child = getattr(node, key, None)
            if isinstance(child, list):
                for item in child:
                    if hasattr(item, '__dict__') and not isinstance(item, token_type()):
                        walk(item, depth + 1)
                    elif isinstance(item, tuple):
                        for part in item:
                            if hasattr(part, '__dict__'):
                                walk(part, depth + 1)
            elif hasattr(child, '__dict__'):
                walk(child, depth + 1)

    walk(program)


def token_type():
    from interpreter.lexer import Token
    return Token


def run_file(filepath):
    with open(filepath, 'r') as f:
        source = f.read()
    evaluator = create_evaluator(script_dir=os.path.dirname(os.path.abspath(filepath)))
    try:
        run_source(source, evaluator)
    except EppError as e:
        _fail(str(e))
    except KeyboardInterrupt:
        print("\n(interrupted)", file=sys.stderr)
        sys.exit(130)


def repl():
    print(BANNER)
    evaluator = create_evaluator()
    buffer = []
    while True:
        try:
            prompt = '... ' if buffer else 'e++> '
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print('\nBye!')
            break

        stripped = line.strip()
        if not buffer:
            if stripped in ('exit', 'quit'):
                print('Bye!')
                break
            elif stripped == 'help':
                print(HELP_TEXT)
                continue
            elif stripped == 'clear':
                print('\033[2J\033[H', end='')
                continue
            elif stripped == 'vars':
                names = sorted(k for k in evaluator.global_scope
                               if not k.startswith('_') and not callable(evaluator.global_scope[k])
                               or isinstance(evaluator.global_scope[k], (int, float, str, list, dict)))
                for name in names:
                    value = evaluator.global_scope[name]
                    print(f"  {name} = {value}")
                continue

        buffer.append(line)
        source = '\n'.join(buffer)

        # Keep collecting while braces/brackets are open or line ends with ':'
        opens = sum(source.count(c) for c in '([{')
        closes = sum(source.count(c) for c in ')]}')
        if opens > closes or source.rstrip().endswith(':'):
            continue

        buffer = []
        if not stripped:
            continue
        try:
            result = run_source(source, evaluator)
            if result is not None and not isinstance(source.strip(), str) \
                    and not source.lstrip().startswith(('say', 'window', 'label', 'button',
                                                        'input', 'image', 'textbox', 'checkbox',
                                                        'dropdown', 'canvas', 'draw', 'slider',
                                                        'progress', 'alert', 'show_window')):
                print(evaluator.to_display_string(result))
        except EppError as e:
            print(str(e))
        except Exception as e:
            print(f"Unexpected error: {e}")


def main():
    args = sys.argv[1:]

    if not args:
        repl()
        return

    if args[0] in ('--version', '-v'):
        from interpreter import __version__
        print(f"E++ v{__version__}")
        return

    if args[0] == '--check':
        if len(args) < 2:
            print("Usage: epp --check <file.epp> [--json]", file=sys.stderr)
            sys.exit(2)
        as_json = '--json' in args[2:]
        sys.exit(check_file(args[1], as_json=as_json))

    if args[0] == '--tokens':
        if len(args) < 2:
            print("Usage: epp --tokens <file.epp>", file=sys.stderr)
            sys.exit(2)
        with open(args[1]) as f:
            dump_tokens(f.read())
        return

    if args[0] == '--ast':
        if len(args) < 2:
            print("Usage: epp --ast <file.epp>", file=sys.stderr)
            sys.exit(2)
        with open(args[1]) as f:
            dump_ast(f.read())
        return

    if args[0] == '-e':
        if len(args) < 2:
            print("Usage: epp -e \"<code>\"", file=sys.stderr)
            sys.exit(1)
        evaluator = create_evaluator()
        try:
            run_source(args[1], evaluator)
        except EppError as e:
            _fail(str(e))
        return

    filepath = args[0]
    if not filepath.endswith('.epp'):
        _fail("Error: e++ files should end with .epp")
    if not os.path.exists(filepath):
        _fail(f"Error: File '{filepath}' not found")
    run_file(filepath)


if __name__ == '__main__':
    main()
