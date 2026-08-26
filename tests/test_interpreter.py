"""Comprehensive E++ interpreter test suite.

Run with:  python3 -m unittest discover -s tests -v
"""
import io
import os
import sys
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interpreter.lexer import Lexer, SOFT_KEYWORD_TYPES
from interpreter.parser import Parser
from interpreter.evaluator import Evaluator
from interpreter.stdlib import make_stdlib
from interpreter.errors import EppError, LexerError, ParserError, EvalError


def parse(source):
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


def evaluate(source, stdin_text=None):
    """Run source through the full pipeline, capturing say output."""
    evaluator = Evaluator()
    evaluator.register_stdlib(make_stdlib(evaluator))
    out_buf = io.StringIO()
    in_buf = io.StringIO(stdin_text if stdin_text is not None else '')
    real_stdin = sys.stdin
    sys.stdin = in_buf
    try:
        with redirect_stdout(out_buf):
            evaluator.run(source)
    finally:
        sys.stdin = real_stdin
    evaluator.captured_output = out_buf.getvalue()
    return evaluator


class TestLexer(unittest.TestCase):
    def tokenize(self, source):
        return Lexer(source).tokenize()

    def test_tokenize_simple(self):
        tokens = self.tokenize('say "Hello"')
        self.assertEqual(tokens[0].type, 'SAY')
        self.assertEqual(tokens[1].value, 'Hello')

    def test_numbers(self):
        tokens = self.tokenize('x = 42\ny = 3.14')
        number_tokens = [t for t in tokens if t.type == 'NUMBER']
        values = [t.value for t in number_tokens]
        self.assertIn(42, values)
        self.assertIn(3.14, values)

    def test_keywords_case_insensitive(self):
        tokens = self.tokenize('IF TRUE')
        self.assertEqual(tokens[0].type, 'IF')
        self.assertEqual(tokens[1].type, 'TRUE')

    def test_comparison_operators_english(self):
        tokens = self.tokenize('x is greater than or equal to y')
        types = [t.type for t in tokens]
        self.assertIn('IS_GREATER_EQUAL', types)

    def test_symbolic_operators(self):
        for symbol in ('==', '!=', '>=', '<=', '>', '<'):
            tokens = [t for t in self.tokenize(f'1 {symbol} 2') if t.type != 'EOF']
            self.assertEqual(len(tokens), 3, f'{symbol} should lex as one operator')
            self.assertNotEqual(tokens[1].type, 'NUMBER')

    def test_modulo_and_power(self):
        tokens = self.tokenize('17 % 5')
        self.assertEqual(tokens[1].type, 'MOD')
        tokens = self.tokenize('2 ^ 10')
        self.assertEqual(tokens[1].type, 'POW')

    def test_compound_assignment(self):
        tokens = self.tokenize('x += 1')
        self.assertEqual(tokens[1].type, 'PLUS_ASSIGN')

    def test_string_escapes(self):
        tokens = self.tokenize(r'"line1\nline2\ttabbed"')
        self.assertEqual(tokens[0].value, 'line1\nline2\ttabbed')

    def test_comments_both_styles(self):
        tokens = self.tokenize('# hash comment\nsay 1 // slash comment')
        types = [t.type for t in tokens]
        self.assertNotIn('NEWLINE', types)  # comment-only line produces nothing

    def test_multilevel_indent(self):
        source = 'if true:\n    if true:\n        say "deep"'
        tokens = self.tokenize(source)
        indents = [t for t in tokens if t.type == 'INDENT']
        dedents = [t for t in tokens if t.type == 'DEDENT']
        self.assertEqual(len(indents), 2)
        self.assertEqual(len(dedents), 2)

    def test_unterminated_string_raises(self):
        with self.assertRaises(LexerError):
            self.tokenize('"never closed')

    def test_unexpected_character_raises(self):
        with self.assertRaises(LexerError):
            self.tokenize('x @ y')


class TestParser(unittest.TestCase):
    def test_parse_assignment(self):
        program = parse('x = 10')
        self.assertEqual(len(program.statements), 1)

    def test_parse_function(self):
        program = parse('func greet(name):\n    say name')
        self.assertEqual(program.statements[0].name, 'greet')
        self.assertEqual(program.statements[0].params, ['name'])

    def test_parse_if_elif_else(self):
        program = parse(
            'if x > 10:\n    pass\nelif x == 5:\n    pass\nelse:\n    pass'
        )
        stmt = program.statements[0]
        self.assertEqual(len(stmt.alternates), 1)
        self.assertIsNotNone(stmt.else_body)

    def test_index_access_parsed(self):
        program = parse('say numbers[0]')
        from interpreter.nodes import SayStmt, IndexAccess
        expr = program.statements[0].expr
        self.assertIsInstance(expr, IndexAccess)

    def test_nested_index_and_member(self):
        program = parse('x = data["items"][2]')
        from interpreter.nodes import IndexAccess, Assignment
        value = program.statements[0].value
        self.assertIsInstance(value, IndexAccess)
        self.assertIsInstance(value.obj, IndexAccess)

    def test_repeat_statement(self):
        program = parse('repeat 5 times:\n    say "hi"')
        self.assertEqual(program.statements[0].__class__.__name__, 'RepeatStmt')

    def test_switch_statement(self):
        program = parse(
            'switch x:\n'
            '    case 1, 2:\n'
            '        say "low"\n'
            '    case 3:\n'
            '        say "three"\n'
            '    default:\n'
            '        say "other"'
        )
        stmt = program.statements[0]
        self.assertEqual(len(stmt.cases), 2)
        self.assertIsNotNone(stmt.default_body)

    def test_bare_try_allowed(self):
        program = parse('try:\n    say 1')
        self.assertIsNone(program.statements[0].catch_body)

    def test_catch_without_var_allowed(self):
        program = parse('try:\n    say 1\ncatch:\n    say 2')
        self.assertIsNone(program.statements[0].catch_var)

    def test_soft_keyword_as_variable(self):
        # text/color/width etc are usable as ordinary identifiers
        program = parse('text = "hi"\ncolor = "red"\nwidth = 100')
        self.assertEqual(len(program.statements), 3)

    def test_input_call_expression(self):
        program = parse('name = input("Who? ")')
        from interpreter.nodes import FuncCall
        self.assertIsInstance(program.statements[0].value, FuncCall)
        self.assertEqual(program.statements[0].value.name, 'input')

    def test_unary_minus(self):
        program = parse('x = -5')
        from interpreter.nodes import UnaryOp
        self.assertIsInstance(program.statements[0].value, UnaryOp)

    def test_compound_assign_desugars(self):
        from interpreter.nodes import Assignment, BinaryOp
        program = parse('count += 5')
        stmt = program.statements[0]
        self.assertIsInstance(stmt, Assignment)
        self.assertIsInstance(stmt.value, BinaryOp)
        self.assertEqual(stmt.value.operator, '+')

    def test_window_accepts_id(self):
        program = parse('window "T" width 400 height 300 color "white" id "win"')
        self.assertIsNotNone(program.statements[0].widget_id)


class TestEvaluator(unittest.TestCase):
    def out(self, evaluator):
        return evaluator.captured_output

    def test_arithmetic(self):
        ev = evaluate('x = 5 + 3 * 2')
        self.assertEqual(ev.global_scope['x'], 11)

    def test_integer_division_stays_int(self):
        ev = evaluate('x = 10 / 2')
        self.assertEqual(ev.global_scope['x'], 5)

    def test_division_by_zero_friendly_error(self):
        with self.assertRaises(EvalError) as cm:
            evaluate('y = 1 / 0')
        self.assertIn('divide by zero', str(cm.exception))

    def test_modulo(self):
        ev = evaluate('x = 17 % 5')
        self.assertEqual(ev.global_scope['x'], 2)

    def test_power(self):
        ev = evaluate('x = 2 ^ 10')
        self.assertEqual(ev.global_scope['x'], 1024)

    def test_unary_minus(self):
        ev = evaluate('x = -7 + 3')
        self.assertEqual(ev.global_scope['x'], -4)

    # Symbolic comparisons — all previously crashed!
    def test_all_comparisons_work(self):
        cases = [
            ('1 < 2', True), ('2 <= 2', True), ('3 > 4', False),
            ('4 >= 4', True), ('5 == 5', True), ('5 != 4', True),
            ('1 is less than 2', True), ('3 is greater than or equal to 3', True),
            ('a is equal to b', False), ('a is not equal to b', True),
        ]
        for i, (expr, expected) in enumerate(cases):
            ev = evaluate(f'a = 1\nb = 2\nresult_{i} = {expr}')
            self.assertEqual(ev.global_scope[f'result_{i}'], expected,
                             f'Failed comparison: {expr}')

    # Indexing — previously not even parsed!
    def test_list_indexing(self):
        ev = evaluate('numbers = [1, 2, 3]\nx = numbers[0]')
        self.assertEqual(ev.global_scope['x'], 1)

    def test_negative_indexing(self):
        ev = evaluate('numbers = [1, 2, 3]\nx = numbers[-1]')
        self.assertEqual(ev.global_scope['x'], 3)

    def test_dict_indexing(self):
        ev = evaluate('person = {"name": "Alice"}\nx = person["name"]')
        self.assertEqual(ev.global_scope['x'], 'Alice')

    def test_index_assignment(self):
        ev = evaluate('l = [1, 2, 3]\nl[1] = 99')
        self.assertEqual(ev.global_scope['l'], [1, 99, 3])

    def test_nested_index_chains(self):
        ev = evaluate('data = {"items": [10, [20, 30]]}\nx = data["items"][1][0]')
        self.assertEqual(ev.global_scope['x'], 20)

    def test_index_out_of_range_message(self):
        with self.assertRaises(EvalError) as cm:
            evaluate('l = [1]\nx = l[5]')
        self.assertIn('out of range', str(cm.exception))

    # Compound assignment
    def test_compound_assignment(self):
        ev = evaluate('c = 10\nc += 5\nc -= 3\nc *= 2\nc %= 7')
        self.assertEqual(ev.global_scope['c'], 3)

    # String interpolation
    def test_interpolation_simple(self):
        ev = evaluate('name = "World"\nsay "Hello {name}!"')
        self.assertEqual(self.out(ev).strip(), 'Hello World!')

    def test_interpolation_expression(self):
        ev = evaluate('say "sum is {40 + 2}"')
        self.assertEqual(self.out(ev).strip(), 'sum is 42')

    def test_interpolation_method(self):
        ev = evaluate('user = {"name": "Zoe"}\nsay "Hi {user[\'name\']}"')
        self.assertEqual(self.out(ev).strip(), 'Hi Zoe')

    def test_literal_braces_survive_invalid_expr(self):
        ev = evaluate('say "curly {not valid !!!} stays"')
        self.assertEqual(self.out(ev).strip(), 'curly {not valid !!!} stays')

    # Loops & control flow
    def test_for_loop(self):
        ev = evaluate('total = 0\nfor i in range(3):\n    total += 1')
        self.assertEqual(ev.global_scope['total'], 3)

    def test_while_loop(self):
        ev = evaluate('c = 0\nwhile c < 3:\n    c += 1')
        self.assertEqual(ev.global_scope['c'], 3)

    def test_repeat_loop(self):
        ev = evaluate('n = 0\nrepeat 4 times:\n    n += 1')
        self.assertEqual(ev.global_scope['n'], 4)

    def test_break_continue(self):
        source = (
            'hits = ""\n'
            'for i in range(10):\n'
            '    if i == 2:\n'
            '        continue\n'
            '    if i == 5:\n'
            '        break\n'
            '    hits += str(i)\n'
        )
        ev = evaluate(source)
        self.assertEqual(ev.global_scope['hits'], '0134')

    def test_break_in_while(self):
        ev = evaluate('i = 0\nwhile true:\n    i += 1\n    if i == 7:\n        break')
        self.assertEqual(ev.global_scope['i'], 7)

    def test_switch_execution(self):
        source = (
            'day = "Tue"\n'
            'mood = ""\n'
            'switch day:\n'
            '    case "Mon", "Tue":\n'
            '        mood = "busy"\n'
            '    default:\n'
            '        mood = "chill"\n'
        )
        ev = evaluate(source)
        self.assertEqual(ev.global_scope['mood'], 'busy')

    def test_switch_default_only_match(self):
        source = (
            'day = "Fri"\n'
            'mood = ""\n'
            'switch day:\n'
            '    case "Mon":\n'
            '        mood = "ugh"\n'
            '    default:\n'
            '        mood = "ok"\n'
        )
        ev = evaluate(source)
        self.assertEqual(ev.global_scope['mood'], 'ok')

    # try/catch semantics
    def test_return_inside_try_not_swallowed(self):
        source = (
            'func answer():\n'
            '    try:\n'
            '        return 42\n'
            '    catch e:\n'
            '        return 0\n'
            'x = answer()'
        )
        ev = evaluate(source)
        self.assertEqual(ev.global_scope['x'], 42)

    def test_bare_try_does_not_crash(self):
        source = (
            'try:\n'
            '    boom()\n'
            'say "still alive"'
        )
        ev = evaluate(source)
        self.assertIn('still alive', self.out(ev))

    def test_catch_binds_error(self):
        source = (
            'msg = ""\n'
            'try:\n'
            '    y = 1 / 0\n'
            'catch err:\n'
            '    msg = "caught"\n'
        )
        ev = evaluate(source)
        self.assertEqual(ev.global_scope['msg'], 'caught')

    # Functions, scoping, classes
    def test_function_args_and_return(self):
        ev = evaluate('func add(a, b):\n    return a + b\nr = add(3, 4)')
        self.assertEqual(ev.global_scope['r'], 7)

    def test_wrong_arg_count_is_friendly(self):
        with self.assertRaises(EvalError) as cm:
            evaluate('func f(a):\n    return a\nf(1, 2)')
        self.assertIn('expects', str(cm.exception))

    def test_recursion(self):
        ev = evaluate(
            'func fib(n):\n'
            '    if n <= 1:\n'
            '        return n\n'
            '    return fib(n - 1) + fib(n - 2)\n'
            'r = fib(10)'
        )
        self.assertEqual(ev.global_scope['r'], 55)

    def test_global_mutation_visible_in_function(self):
        source = (
            'counter = 0\n'
            'func bump():\n'
            '    counter += 1\n'
            'bump()\n'
            'bump()'
        )
        ev = evaluate(source)
        self.assertEqual(ev.global_scope['counter'], 2)

    def test_class_method_with_arguments(self):
        source = (
            'class Greeter:\n'
            '    func init(name):\n'
            '        self.name = name\n'
            '    func shout(word):\n'
            '        return self.name + " says " + word + "!"\n'
            'g = Greeter("Bob")\n'
            'r = g.shout("hello")'
        )
        ev = evaluate(source)
        self.assertEqual(ev.global_scope['r'], 'Bob says hello!')

    def test_constructor_arg_count_enforced(self):
        with self.assertRaises(EvalError):
            evaluate('class P:\n    func init(a):\n        self.a = a\nP(1, 2)')

    def test_list_methods(self):
        source = (
            'l = [3, 1, 2]\n'
            'l.push(9)\n'
            'top = l.pop()\n'
            'has_two = l.contains(2)\n'
            'idx = l.index_of(2)'
        )
        ev = evaluate(source)
        self.assertEqual(top := ev.global_scope['top'], 9)
        self.assertTrue(ev.global_scope['has_two'])
        self.assertEqual(ev.global_scope['idx'], 2)

    def test_string_methods(self):
        ev = evaluate(
            's = "Hello World"\n'
            'u = s.upper()\n'
            'l = s.lower()\n'
            'c = s.contains("World")\n'
            'sw = s.starts_with("He")'
        )
        self.assertEqual(ev.global_scope['u'], 'HELLO WORLD')
        self.assertEqual(ev.global_scope['l'], 'hello world')
        self.assertTrue(ev.global_scope['c'])
        self.assertTrue(ev.global_scope['sw'])

    def test_soft_keyword_variables_round_trip(self):
        ev = evaluate('text = "hi"\ncolor = "red"\nwidth = 42\nsay "{text}/{color}/{width}"')
        self.assertIn('hi/red/42', self.out(ev))

    def test_truthiness(self):
        ev = evaluate('results = []\nif 0:\n    results.push(false)\nif "":\n    results.push(false)\nif [1]:\n    results.push(true)')
        self.assertEqual(ev.global_scope['results'], [True])

    def test_say_number_formatting(self):
        ev = evaluate('say 5\nsay 2.5\nsay true')
        lines = self.out(ev).splitlines()
        self.assertEqual(lines, ['5', '2.5', 'true'])


class TestStdLib(unittest.TestCase):
    def out(self, evaluator):
        return evaluator.captured_output

    def test_len_range_str_int_type(self):
        ev = evaluate(
            'a = len([1, 2, 3])\n'
            'b = range(3)\n'
            'c = str(42)\n'
            'd = int("42")\n'
            'e = type(3.14)'
        )
        self.assertEqual(ev.global_scope['a'], 3)
        self.assertEqual(ev.global_scope['b'], [0, 1, 2])
        self.assertEqual(ev.global_scope['c'], '42')
        self.assertEqual(ev.global_scope['d'], 42)
        self.assertEqual(ev.global_scope['e'], 'float')

    def test_range_start_stop_step(self):
        ev = evaluate('x = range(2, 10, 3)')
        self.assertEqual(ev.global_scope['x'], [2, 5, 8])

    def test_sort_reversed_sum_min_max(self):
        ev = evaluate(
            'nums = [3, 1, 2]\n'
            's = sort(nums)\n'
            'r = reversed(nums)\n'
            't = sum(nums)\n'
            'lo = min(nums)\n'
            'hi = max(nums)'
        )
        self.assertEqual(ev.global_scope['s'], [1, 2, 3])
        self.assertEqual(ev.global_scope['r'], [2, 1, 3])
        self.assertEqual(ev.global_scope['t'], 6)
        self.assertEqual(ev.global_scope['lo'], 1)
        self.assertEqual(ev.global_scope['hi'], 3)

    def test_random_int_bounds(self):
        ev = evaluate('found_valid = false\nv = random_int(5, 5)')
        self.assertEqual(ev.global_scope['v'], 5)

    def test_json_roundtrip(self):
        source = (
            'obj = {"list": [1, 2], "ok": true}\n'
            'text = to_json(obj)\n'
            'back = parse_json(text)\n'
            'same = back["list"][1]'
        )
        ev = evaluate(source)
        self.assertEqual(ev.global_scope['same'], 2)

    def test_file_io_roundtrip(self):
        path = os.path.join('/tmp', 'epp_test_file.txt')
        if os.path.exists(path):
            os.remove(path)
        source = (
            f'write_file "{path}", "hello"\n'
            f'append_file "{path}", " world"\n'
            f'text = read_file "{path}"\n'
            f'here = exists "{path}"\n'
            f'delete_file "{path}"'
        )
        ev = evaluate(source)
        self.assertEqual(ev.global_scope['text'], 'hello world')
        self.assertTrue(ev.global_scope['here'])
        self.assertFalse(os.path.exists(path))

    def test_upper_lower_trim(self):
        ev = evaluate('a = upper("abc")\nb = lower("ABC")\nc = trim("  pad  ")')
        self.assertEqual((ev.global_scope['a'], ev.global_scope['b'],
                          ev.global_scope['c']), ('ABC', 'abc', 'pad'))


class TestImports(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp(prefix='epp_import_')
        with open(os.path.join(self.tmp, 'helper.epp'), 'w') as f:
            f.write('magic = 42\nfunc double(n):\n    return n * 2\n')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_import_relative_to_script(self):
        main_path = os.path.join(self.tmp, 'main.epp')
        with open(main_path, 'w') as f:
            f.write('import "helper.epp"\nr = double(magic)')
        ev = Evaluator()
        ev.register_stdlib(make_stdlib(ev))
        ev.script_dir = self.tmp
        with open(main_path) as f:
            src = f.read()
        import io
        from contextlib import redirect_stdout
        with redirect_stdout(io.StringIO()):
            ev.run(src)
        self.assertEqual(ev.global_scope['r'], 84)

    def test_circular_import_detected(self):
        with open(os.path.join(self.tmp, 'a.epp'), 'w') as f:
            f.write('import "b.epp"\n')
        with open(os.path.join(self.tmp, 'b.epp'), 'w') as f:
            f.write('import "a.epp"\n')
        ev = Evaluator()
        ev.register_stdlib(make_stdlib(ev))
        ev.script_dir = self.tmp
        with self.assertRaises(EvalError) as cm:
            ev.run('import "a.epp"')
        self.assertIn('Circular', str(cm.exception))


class TestErrorMessages(unittest.TestCase):
    def test_undefined_variable_has_suggestion(self):
        with self.assertRaises(EvalError) as cm:
            evaluate('say undefined_thing')
        self.assertIn('not defined', str(cm.exception))

    def test_parser_error_mentions_line(self):
        with self.assertRaises(ParserError) as cm:
            parse('if x >\n    say "broken"')
        self.assertIn('line', str(cm.exception))

    def test_unknown_widget_error(self):
        with self.assertRaises(EvalError) as cm:
            evaluate('''set_text "nope" to "x"''')
        self.assertIn("not found", str(cm.exception))


class TestRegressionExamples(unittest.TestCase):
    """Guard against regressions in shipped example programs."""

    def run_example(self, relpath):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base, 'tests', 'examples', relpath)
        with open(path) as f:
            return evaluate(f.read())

    def test_hello(self):
        ev = self.run_example('hello.epp')
        self.assertIn('Hello, World!', ev.captured_output)

    def test_fibonacci(self):
        ev = self.run_example('fibonacci.epp')
        self.assertIn('fib(9) = 34', ev.captured_output)

    def test_classes(self):
        ev = self.run_example('classes.epp')
        self.assertIn('Count: 3', ev.captured_output)

    def test_collections_now_correct(self):
        ev = self.run_example('collections.epp')
        self.assertIn('First number: 1', ev.captured_output)
        self.assertIn('Name: Alice', ev.captured_output)

    def test_input_test_parses(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base, 'tests', 'examples', 'input_test.epp')
        with open(path) as f:
            ev = evaluate(f.read(), stdin_text='Tester\n21\n')
        self.assertIn('Hello, Tester!', ev.captured_output)
        self.assertIn('You are an adult!', ev.captured_output)


class TestRound2Features(unittest.TestCase):
    """v2.1 features: positions, membership, format specs, dict.get."""

    def out(self, evaluator):
        return evaluator.captured_output

    def test_membership_in(self):
        ev = evaluate('l = [1, 2, 3]\nr = 2 in l')
        self.assertTrue(ev.global_scope['r'])

    def test_membership_not_in(self):
        ev = evaluate('l = [1, 2, 3]\nr = 9 not in l')
        self.assertTrue(ev.global_scope['r'])

    def test_membership_string_and_dict(self):
        source = (
            'a = "ell" in "Hello"\n'
            'd = {"k": 1}\n'
            'b = "k" in d\n'
            'c = "x" not in d'
        )
        ev = evaluate(source)
        self.assertEqual((ev.global_scope['a'], ev.global_scope['b'],
                          ev.global_scope['c']), (True, True, True))

    def test_membership_invalid_target_message(self):
        with self.assertRaises(EvalError) as cm:
            evaluate('r = 1 in 5')
        self.assertIn('list, string or dictionary', str(cm.exception))

    def test_format_spec_float(self):
        ev = evaluate('pi = 3.14159\nsay "pi={pi:.2f}"')
        self.assertIn('pi=3.14', self.out(ev))

    def test_format_spec_zero_pad_and_thousands(self):
        ev = evaluate('say "{7:03d} {1234567:,}"')
        self.assertIn('007 1,234,567', self.out(ev))

    def test_format_spec_with_colon_in_string_still_works(self):
        ev = evaluate('d = {"a:b": 5}\nsay "{d[\'a:b\']}"')
        self.assertIn('5', self.out(ev))

    def test_runtime_error_has_line_number(self):
        with self.assertRaises(EvalError) as cm:
            evaluate('a = 1\nb = 2\nc = a + ghost')
        err = cm.exception
        self.assertIsNotNone(err.line)
        self.assertGreaterEqual(err.line, 3)

    def test_error_line_survives_function_call(self):
        source = (
            'func go():\n'
            '    return nothing_here\n'
            '\n'
            'x = go()'
        )
        with self.assertRaises(EvalError) as cm:
            evaluate(source)
        self.assertEqual(cm.exception.line, 2)

    def test_dict_get_method(self):
        source = (
            'd = {"name": "Ada"}\n'
            'a = d.get("name")\n'
            'b = d.get("missing")\n'
            'c = d.get("missing", "fallback")'
        )
        ev = evaluate(source)
        self.assertEqual(ev.global_scope['a'], 'Ada')
        self.assertIsNone(ev.global_scope['b'])
        self.assertEqual(ev.global_scope['c'], 'fallback')

    def test_check_mode_json(self):
        import json
        import subprocess
        import tempfile
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with tempfile.NamedTemporaryFile('w', suffix='.epp', delete=False) as f:
            f.write('x = 1\nfor i in:\n')
            path = f.name
        try:
            proc = subprocess.run(
                [sys.executable, '-m', 'interpreter.epp', '--check', path, '--json'],
                capture_output=True, text=True,
                cwd=base
            )
            payload = None
            for line in proc.stdout.splitlines():
                line = line.strip()
                if line.startswith('{'):
                    payload = json.loads(line)
                    break
            self.assertIsNotNone(payload, f'no JSON in output: {proc.stdout!r} {proc.stderr!r}')
            self.assertFalse(payload['ok'])
            self.assertGreaterEqual(payload['errors'][0]['line'], 1)
        finally:
            os.unlink(path)


    def test_string_shorthand_call(self):
        source = (
            'write_file "/tmp/epp_sh.txt", "hi"\n'
            'r = read_file "/tmp/epp_sh.txt"'
        )
        ev = evaluate(source)
        self.assertEqual(ev.global_scope['r'], 'hi')

    def test_paren_calls_with_variables(self):
        source = (
            'func double(n):\n'
            '    return n * 2\n'
            'x = 21\n'
            'r = double(x)'
        )
        ev = evaluate(source)
        self.assertEqual(ev.global_scope['r'], 42)

    def test_minus_stays_subtraction_not_arg(self):
        ev = evaluate('total = 10\nr = total - 1')
        self.assertEqual(ev.global_scope['r'], 9)

    def test_list_insert_and_unshift(self):
        source = (
            'l = [2, 3]\n'
            'insert(l, 0, 1)\n'
            'l.unshift(0)\n'
            'l.insert(2, 1.5)'
        )
        ev = evaluate(source)
        self.assertEqual(ev.global_scope['l'], [0, 1, 1.5, 2, 3])

    def test_on_key_parses_on_window_and_canvas(self):
        program = parse(
            'window "G" width 100 height 100 on_key handle\n'
            'canvas "cv" width 50 height 50 color "black" on_key handle'
        )
        self.assertEqual(program.statements[0].on_key, 'handle')
        self.assertEqual(program.statements[1].on_key, 'handle')


    def test_expect_to_be_pass_and_fail(self):
        ev = evaluate('test "t":\n    expect 2 + 2 to_be 4')
        self.assertEqual(ev.test_stats['passed'], 1)
        self.assertEqual(ev.test_stats['failed'], 0)

        ev = evaluate('test "t":\n    expect 1 + 1 to_be 3')
        self.assertEqual(ev.test_stats['failed'], 1)
        self.assertIn('expected 3, got 2', ev.captured_output)

    def test_expect_matchers(self):
        source = (
            'test "matchers":\n'
            '    expect true to_be_true\n'
            '    expect 0 to_be_false\n'
            '    expect 1 / 0 to_throw'
        )
        ev = evaluate(source)
        self.assertEqual(ev.test_stats['passed'], 3)

    def test_float_tolerance_in_expect(self):
        ev = evaluate('test "floats":\n    expect 0.1 + 0.2 to_be 0.3')
        self.assertEqual(ev.test_stats['failed'], 0)

    def test_failing_tests_summary(self):
        ev = evaluate(
            'test "a":\n    expect 1 to_be 1\n'
            'test "b":\n    expect 1 to_be 2'
        )
        self.assertIn('1 passed, 1 failed', ev.captured_output)

    def test_on_key_parses_on_widgets(self):
        program = parse(
            'input "box" at 0 0 on_key typed\n'
            'textbox "tb" at 0 40 on_key typed\n'
            'button "Go" at 0 80 on_key keyed'
        )
        self.assertEqual(program.statements[0].on_key, 'typed')
        self.assertEqual(program.statements[1].on_key, 'typed')
        self.assertEqual(program.statements[2].on_key, 'keyed')

    def test_version_flag(self):
        import subprocess
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        proc = subprocess.run(
            [sys.executable, '-m', 'interpreter.epp', '--version'],
            capture_output=True, text=True, cwd=base
        )
        self.assertIn('E++ v', proc.stdout)


if __name__ == '__main__':
    unittest.main()
