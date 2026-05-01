import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interpreter.lexer import Lexer
from interpreter.parser import Parser
from interpreter.evaluator import Evaluator
from interpreter.stdlib import make_stdlib

class TestLexer(unittest.TestCase):
    def test_tokenize_simple(self):
        source = 'say "Hello"'
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        self.assertEqual(tokens[0].type, 'SAY')
        self.assertEqual(tokens[1].type, 'STRING')
        self.assertEqual(tokens[1].value, 'Hello')

    def test_tokenize_number(self):
        source = 'x = 42'
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        self.assertEqual(tokens[2].type, 'NUMBER')
        self.assertEqual(tokens[2].value, 42)

    def test_tokenize_float(self):
        source = 'pi = 3.14'
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        self.assertEqual(tokens[2].type, 'NUMBER')
        self.assertEqual(tokens[2].value, 3.14)

    def test_tokenize_keywords(self):
        source = 'if else for while func class'
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        keyword_types = ['IF', 'ELSE', 'FOR', 'WHILE', 'FUNC', 'CLASS']
        for i, kt in enumerate(keyword_types):
            self.assertEqual(tokens[i].type, kt)

    def test_comparison_operators(self):
        source = 'x is greater than y'
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        self.assertEqual(tokens[1].type, 'IS_GREATER_THAN')


class TestParser(unittest.TestCase):
    def test_parse_assignment(self):
        source = 'x = 10'
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        self.assertEqual(len(program.statements), 1)

    def test_parse_function(self):
        source = '''func greet(name):
    say name'''
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        self.assertEqual(len(program.statements), 1)

    def test_parse_if(self):
        source = '''if x is greater than 10:
    say "big"
else:
    say "small"'''
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        self.assertEqual(len(program.statements), 1)


class TestEvaluator(unittest.TestCase):
    def eval_source(self, source):
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        evaluator = Evaluator()
        stdlib = make_stdlib(evaluator)
        evaluator.register_stdlib(stdlib)
        evaluator.run(source)
        return evaluator

    def test_assignment(self):
        evaluator = self.eval_source('x = 10')
        self.assertIn('x', evaluator.global_scope)
        self.assertEqual(evaluator.global_scope['x'], 10)

    def test_arithmetic(self):
        evaluator = self.eval_source('x = 5 + 3')
        self.assertEqual(evaluator.global_scope['x'], 8)

    def test_string_concat(self):
        evaluator = self.eval_source('x = "Hello" + " World"')
        self.assertEqual(evaluator.global_scope['x'], 'Hello World')

    def test_comparison_greater(self):
        evaluator = self.eval_source('x = 10 is greater than 5')
        self.assertEqual(evaluator.global_scope['x'], True)

    def test_comparison_less(self):
        evaluator = self.eval_source('x = 3 is less than 5')
        self.assertEqual(evaluator.global_scope['x'], True)

    def test_comparison_equal(self):
        evaluator = self.eval_source('x = 5 is 5')
        self.assertEqual(evaluator.global_scope['x'], True)

    def test_comparison_not_equal(self):
        evaluator = self.eval_source('x = 5 is not 3')
        self.assertEqual(evaluator.global_scope['x'], True)

    def test_if_true(self):
        source = '''x = 0
if 1 is 1:
    x = 10'''
        evaluator = self.eval_source(source)
        self.assertEqual(evaluator.global_scope['x'], 10)

    def test_for_loop(self):
        source = '''total = 0
for i in range(3):
    total = total + 1'''
        evaluator = self.eval_source(source)
        self.assertEqual(evaluator.global_scope['total'], 3)

    def test_while_loop(self):
        source = '''count = 0
while count is less than 3:
    count = count + 1'''
        evaluator = self.eval_source(source)
        self.assertEqual(evaluator.global_scope['count'], 3)

    def test_function(self):
        source = '''func add(a, b):
    return a + b

result = add(3, 4)'''
        evaluator = self.eval_source(source)
        self.assertEqual(evaluator.global_scope['result'], 7)

    def test_say(self):
        evaluator = self.eval_source('say "test"')
        self.assertEqual(evaluator.output, ['test'])

    def test_list(self):
        evaluator = self.eval_source('x = [1, 2, 3]')
        self.assertEqual(evaluator.global_scope['x'], [1, 2, 3])

    def test_dict(self):
        evaluator = self.eval_source('x = {"name": "Alice"}')
        self.assertEqual(evaluator.global_scope['x'], {'name': 'Alice'})


class TestStdLib(unittest.TestCase):
    def eval_source(self, source):
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        evaluator = Evaluator()
        stdlib = make_stdlib(evaluator)
        evaluator.register_stdlib(stdlib)
        evaluator.run(source)
        return evaluator

    def test_len(self):
        evaluator = self.eval_source('x = len([1, 2, 3])')
        self.assertEqual(evaluator.global_scope['x'], 3)

    def test_range(self):
        evaluator = self.eval_source('x = range(5)')
        self.assertEqual(evaluator.global_scope['x'], [0, 1, 2, 3, 4])

    def test_str(self):
        evaluator = self.eval_source('x = str(42)')
        self.assertEqual(evaluator.global_scope['x'], '42')

    def test_int(self):
        evaluator = self.eval_source('x = int("42")')
        self.assertEqual(evaluator.global_scope['x'], 42)

    def test_type(self):
        evaluator = self.eval_source('x = type(42)')
        self.assertEqual(evaluator.global_scope['x'], 'int')


if __name__ == '__main__':
    unittest.main()