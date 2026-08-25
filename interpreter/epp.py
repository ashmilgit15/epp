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


def run_file(filepath):
    with open(filepath, 'r') as f:
        source = f.read()
    evaluator = create_evaluator(script_dir=os.path.dirname(os.path.abspath(filepath)))
    try:
        run_source(source, evaluator)
    except EppError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
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

    if args[0] == '-e':
        if len(args) < 2:
            print("Usage: epp -e \"<code>\"", file=sys.stderr)
            sys.exit(1)
        evaluator = create_evaluator()
        try:
            run_source(args[1], evaluator)
        except EppError as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)
        return

    if args[0] in ('--version', '-v'):
        from interpreter import __version__
        print(f"E++ v{__version__}")
        return

    filepath = args[0]
    if not filepath.endswith('.epp'):
        print("Error: e++ files should end with .epp", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found", file=sys.stderr)
        sys.exit(1)
    run_file(filepath)


if __name__ == '__main__':
    main()
