#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from interpreter.lexer import Lexer
from interpreter.parser import Parser
from interpreter.evaluator import Evaluator
from interpreter.stdlib import make_stdlib
from interpreter.errors import EppError

def main():
    if len(sys.argv) < 2:
        print("Usage: python epp.py <file.epp>")
        print("  or: python epp.py -e <code>")
        sys.exit(1)

    if sys.argv[1] == '-e' and len(sys.argv) > 2:
        source = sys.argv[2]
    else:
        filepath = sys.argv[1]
        if not filepath.endswith('.epp'):
            print(f"Error: e++ files should end with .epp")
            sys.exit(1)
        if not os.path.exists(filepath):
            print(f"Error: File '{filepath}' not found")
            sys.exit(1)
        with open(filepath, 'r') as f:
            source = f.read()

    try:
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        evaluator = Evaluator()
        stdlib = make_stdlib(evaluator)
        evaluator.register_stdlib(stdlib)
        evaluator.run(source)
    except EppError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()