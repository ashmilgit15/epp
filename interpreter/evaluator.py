import os
from interpreter.nodes import *
from interpreter.errors import (EppError, EvalError, ReturnException,
                                BreakException, ContinueException)


class EppInstance:
    def __init__(self, cls, fields=None):
        self.cls = cls
        self.fields = fields or {}

    def get(self, name):
        if name in self.fields:
            return self.fields[name]
        if hasattr(self.cls, name):
            return getattr(self.cls, name)
        raise EvalError(f"'{name}' is not defined in class '{self.cls.name}'")

    def set(self, name, value):
        self.fields[name] = value


class Function:
    def __init__(self, name, params, body, def_stack=None):
        self.name = name
        self.params = params
        self.body = body
        # Snapshot (by reference) of the scope chain at definition time
        self.def_stack = list(def_stack) if def_stack is not None else None

    def __repr__(self):
        return f"<function {self.name}>"


class Class:
    def __init__(self, name, body):
        self.name = name
        self.body = body
        self.methods = {}

    def __repr__(self):
        return f"<class {self.name}>"


class Evaluator:
    def __init__(self, stdlib=None):
        self.global_scope = {}
        self.scope_stack = [self.global_scope]
        self.output = []
        self.import_stack = []      # abs paths currently being imported (cycle detection)
        self.imported_modules = set()  # abs paths already executed
        self.script_dir = os.getcwd()
        if stdlib:
            self.register_stdlib(stdlib)

    # ── Scope helpers ─────────────────────────────────────────────────────────
    @property
    def current_scope(self):
        return self.scope_stack[-1]

    def lookup(self, name):
        for scope in reversed(self.scope_stack):
            if name in scope:
                return True, scope
        return False, None

    def assign_name(self, name, value):
        found, scope = self.lookup(name)
        if found:
            scope[name] = value
        else:
            self.current_scope[name] = value

    def register_stdlib(self, stdlib):
        for name, func in stdlib.items():
            self.global_scope[name] = func

    def eval(self, node):
        method_name = f'eval_{type(node).__name__}'
        method = getattr(self, method_name, None)
        if method is None:
            raise EvalError(f"No evaluator for {type(node).__name__}")
        return method(node)

    def run(self, source, filename=None):
        from interpreter.lexer import Lexer
        from interpreter.parser import Parser
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        return self.eval(program)

    def eval_Program(self, node):
        result = None
        for stmt in node.statements:
            result = self.eval(stmt)
        return result

    # ── Core values ───────────────────────────────────────────────────────────

    def eval_SayStmt(self, node):
        value = self.eval(node.expr)
        text = self.to_display_string(value)
        self.output.append(text)
        print(text)
        return None

    def to_display_string(self, value):
        if isinstance(value, float) and value == int(value):
            return str(value)
        if isinstance(value, bool):
            return 'true' if value else 'false'
        if value is None:
            return 'null'
        return str(value)

    def eval_ExpressionStatement(self, node):
        return self.eval(node.expr)

    def eval_Number(self, node):
        return node.value

    def eval_String(self, node):
        value = node.value
        if '{' in value and '}' in value:
            return self.interpolate(value)
        return value

    def interpolate(self, text):
        """Interpolate {expression} inside strings: "Hello {name}"."""
        result = []
        i = 0
        n = len(text)
        while i < n:
            ch = text[i]
            if ch == '{':
                depth = 1
                j = i + 1
                while j < n and depth > 0:
                    if text[j] == '{':
                        depth += 1
                    elif text[j] == '}':
                        depth -= 1
                    j += 1
                if depth == 0:
                    inner = text[i + 1:j - 1]
                    try:
                        val = self.eval_snippet(inner)
                        result.append(self.to_display_string(val))
                        i = j
                        continue
                    except EppError:
                        pass  # leave literal braces if it isn't a valid expression
                result.append(ch)
                i += 1
            else:
                result.append(ch)
                i += 1
        return ''.join(result)

    def eval_snippet(self, code):
        """Compile & evaluate a tiny expression embedded in a string."""
        from interpreter.lexer import Lexer
        from interpreter.parser import Parser
        tokens = Lexer(code).tokenize()
        expr = Parser(tokens).parse_expression()
        return self.eval(expr)

    def eval_Boolean(self, node):
        return node.value

    def eval_Null(self, node):
        return None

    def eval_Identifier(self, node):
        name = node.name
        found, scope = self.lookup(name)
        if found:
            return scope[name]
        raise EvalError(
            f"'{name}' is not defined",
            suggestion="Did you forget to assign it?"
        )

    def eval_ListLiteral(self, node):
        return [self.eval(e) for e in node.elements]

    def eval_DictLiteral(self, node):
        result = {}
        for k, v in node.pairs:
            key = self.eval(k)
            val = self.eval(v)
            result[key] = val
        return result

    # ── Operators ─────────────────────────────────────────────────────────────

    def eval_Assignment(self, node):
        value = self.eval(node.value)
        self.assign_name(node.name, value)
        return value

    def eval_BinaryOp(self, node):
        left = self.eval(node.left)
        right = self.eval(node.right)
        op = node.operator
        if op == '+':
            if isinstance(left, str) or isinstance(right, str):
                return self.to_display_string(left) + self.to_display_string(right)
            return left + right
        elif op == '-':
            return left - right
        elif op == '*':
            if isinstance(left, str) and isinstance(right, (int, float)):
                return left * int(right)
            return left * right
        elif op == '/':
            if right == 0:
                raise EvalError("Cannot divide by zero")
            result = left / right
            # Keep whole-number divisions as integers: 10 / 2 → 5
            if isinstance(left, int) and isinstance(right, int) \
                    and not isinstance(left, bool) and not isinstance(right, bool) \
                    and result == int(result):
                return int(result)
            return result
        elif op == '%':
            if right == 0:
                raise EvalError("Cannot take modulus by zero")
            return left % right
        elif op == '^':
            return left ** right
        raise EvalError(f"Unknown operator '{op}'")

    def eval_UnaryOp(self, node):
        operand = self.eval(node.operand)
        if node.operator == 'not':
            return not self.is_truthy(operand)
        if node.operator == '-':
            return -operand
        raise EvalError(f"Unknown unary operator '{node.operator}'")

    COMPARISON_MAP = {
        'is': '==',
        'is equal to': '==',
        '==': '==',
        'is not': '!=',
        'is not equal to': '!=',
        '!=': '!=',
        'is greater than': '>',
        '>': '>',
        'is less than': '<',
        '<': '<',
        'is greater than or equal to': '>=',
        '>=': '>=',
        'is less than or equal to': '<=',
        '<=': '<=',
    }

    def eval_Comparison(self, node):
        left = self.eval(node.left)
        right = self.eval(node.right)
        op = self.COMPARISON_MAP.get(node.operator)
        if op == '==':
            return left == right
        elif op == '!=':
            return left != right
        elif op == '>':
            return left > right
        elif op == '<':
            return left < right
        elif op == '>=':
            return left >= right
        elif op == '<=':
            return left <= right
        raise EvalError(
            f"Unknown comparison '{node.operator}'",
            suggestion="Try: is, is not, is greater than, is less than"
        )

    def eval_LogicalOp(self, node):
        left = self.eval(node.left)
        if node.operator == 'and':
            if not self.is_truthy(left):
                return False
            return self.is_truthy(self.eval(node.right))
        elif node.operator == 'or':
            if self.is_truthy(left):
                return True
            return self.is_truthy(self.eval(node.right))
        raise EvalError(f"Unknown logical operator '{node.operator}'")

    # ── Functions & classes ───────────────────────────────────────────────────

    def eval_FuncCall(self, node):
        name = node.name
        found, scope = self.lookup(name)
        if not found:
            raise EvalError(
                f"'{name}' is not defined",
                suggestion="Did you define it with 'func'?"
            )
        func = scope[name]
        args = [self.eval(arg) for arg in node.args]
        if isinstance(func, Function):
            return self.call_function(func, args)
        elif isinstance(func, Class):
            return self.instantiate_class(func, args)
        if callable(func) and not isinstance(func, type):
            if hasattr(func, '_epp_native'):
                return func(self, args)
            return func(*args)
        raise EvalError(f"'{name}' is not a function")

    def call_function(self, func, args):
        if len(args) != len(func.params):
            raise EvalError(
                f"'{func.name}' expects {len(func.params)} argument(s), got {len(args)}",
                suggestion="Check the function definition"
            )
        frame = {}
        for param, arg in zip(func.params, args):
            frame[param] = arg
        base_stack = func.def_stack if func.def_stack is not None else [self.global_scope]
        old_stack = self.scope_stack
        self.scope_stack = base_stack + [frame]
        result = None
        try:
            for stmt in func.body:
                self.eval(stmt)
        except ReturnException as e:
            result = e.value
        finally:
            self.scope_stack = old_stack
        return result

    def eval_FuncDef(self, node):
        func = Function(node.name, node.params, node.body, self.scope_stack)
        self.current_scope[node.name] = func
        return None

    def instantiate_class(self, cls, args):
        instance = EppInstance(cls)
        init_method = cls.methods.get('init')
        if init_method is None and hasattr(cls, 'init'):
            init_method = getattr(cls, 'init')
        if isinstance(init_method, Function):
            if len(args) != len(init_method.params):
                raise EvalError(
                    f"'{cls.name}' expects {len(init_method.params)} argument(s), got {len(args)}"
                )
            frame = {'self': instance}
            for param, arg in zip(init_method.params, args):
                frame[param] = arg
            old_stack = self.scope_stack
            self.scope_stack = (init_method.def_stack or [self.global_scope]) + [frame]
            try:
                for stmt in init_method.body:
                    self.eval(stmt)
            except ReturnException:
                pass
            finally:
                self.scope_stack = old_stack
        elif args:
            raise EvalError(
                f"'{cls.name}' does not take constructor arguments"
            )
        return instance

    def eval_ClassDef(self, node):
        cls = Class(node.name, node.body)
        for stmt in node.body:
            if isinstance(stmt, FuncDef):
                method = Function(stmt.name, stmt.params, stmt.body, self.scope_stack)
                cls.methods[stmt.name] = method
                setattr(cls, stmt.name, method)
        self.current_scope[node.name] = cls
        return None

    def eval_MethodCall(self, node):
        obj = self.eval(node.obj)
        method_name = node.method
        args = [self.eval(arg) for arg in node.args]
        if isinstance(obj, EppInstance):
            method = obj.cls.methods.get(method_name)
            if method is None and method_name in obj.fields:
                method = obj.fields[method_name]
            if isinstance(method, Function):
                if len(args) != len(method.params):
                    raise EvalError(
                        f"Method '{method_name}' expects {len(method.params)} argument(s), got {len(args)}"
                    )
                frame = dict(obj.fields)
                frame['self'] = obj
                for param, arg in zip(method.params, args):
                    frame[param] = arg
                old_stack = self.scope_stack
                self.scope_stack = (method.def_stack or [self.global_scope]) + [frame]
                result = None
                try:
                    for stmt in method.body:
                        self.eval(stmt)
                except ReturnException as e:
                    result = e.value
                finally:
                    self.scope_stack = old_stack
                # persist any new/changed fields written via `self.x`
                return result
            if callable(method):
                return method(*args)
            raise EvalError(
                f"'{method_name}' is not defined in class '{obj.cls.name}'"
            )
        elif isinstance(obj, list):
            return self.handle_list_method(obj, method_name, args)
        elif isinstance(obj, str):
            return self.handle_string_method(obj, method_name, args)
        elif isinstance(obj, dict):
            return self.handle_dict_method(obj, method_name, args)
        raise EvalError(f"Cannot call '{method_name}' on this value")

    def handle_list_method(self, lst, method, args):
        if method == 'push':
            lst.append(args[0] if args else None)
            return None
        elif method == 'pop':
            if lst:
                return lst.pop()
            return None
        elif method in ('len', 'length'):
            return len(lst)
        elif method == 'contains':
            return (args[0] if args else None) in lst
        elif method == 'index_of':
            item = args[0] if args else None
            return lst.index(item) if item in lst else -1
        elif method == 'first':
            return lst[0] if lst else None
        elif method == 'last':
            return lst[-1] if lst else None
        elif method == 'reverse':
            lst.reverse()
            return None
        elif method == 'sort':
            try:
                lst.sort()
            except TypeError:
                raise EvalError("Cannot sort this list — items must be comparable")
            return None
        raise EvalError(
            f"List has no method '{method}'",
            suggestion="Try push, pop, len, contains, index_of, first, last, reverse or sort"
        )

    def handle_string_method(self, s, method, args):
        if method in ('len', 'length'):
            return len(s)
        elif method == 'upper':
            return s.upper()
        elif method == 'lower':
            return s.lower()
        elif method == 'trim':
            return s.strip()
        elif method == 'contains':
            return (args[0] if args else '') in s
        elif method == 'starts_with':
            return s.startswith(args[0] if args else '')
        elif method == 'ends_with':
            return s.endswith(args[0] if args else '')
        elif method == 'replace':
            return s.replace(args[0] if args else '', args[1] if len(args) > 1 else '')
        elif method == 'split':
            return s.split(args[0] if args else ' ')
        elif method == 'index_of':
            sub = args[0] if args else ''
            return s.find(sub)
        raise EvalError(
            f"String has no method '{method}'",
            suggestion="Try upper, lower, trim, contains, starts_with, ends_with, replace, split or index_of"
        )

    def handle_dict_method(self, d, method, args):
        if method in ('len', 'length'):
            return len(d)
        elif method == 'keys':
            return list(d.keys())
        elif method == 'values':
            return list(d.values())
        elif method == 'contains' or method == 'has':
            return (args[0] if args else None) in d
        elif method == 'remove' or method == 'delete':
            d.pop(args[0] if args else None, None)
            return None
        raise EvalError(
            f"Dict has no method '{method}'",
            suggestion="Try keys, values, len, contains or remove"
        )

    def eval_MemberAccess(self, node):
        obj = self.eval(node.obj)
        member = node.member
        if isinstance(obj, EppInstance):
            return obj.get(member)
        elif isinstance(obj, dict):
            if member in obj:
                return obj[member]
            return None
        elif isinstance(obj, list):
            if member in ('len', 'length'):
                return len(obj)
            raise EvalError(f"List has no member '{member}'")
        elif isinstance(obj, str):
            if member in ('len', 'length'):
                return len(obj)
            raise EvalError(f"String has no member '{member}'")
        raise EvalError(f"Cannot access '{member}' of this value")

    def eval_PropertyAssignment(self, node):
        obj = self.eval(node.obj)
        value = self.eval(node.value)
        if isinstance(obj, EppInstance):
            obj.set(node.member, value)
            return value
        elif isinstance(obj, dict):
            obj[node.member] = value
            return value
        raise EvalError(f"Cannot set property '{node.member}' on this value")

    # ── Indexing ──────────────────────────────────────────────────────────────

    def eval_IndexAccess(self, node):
        obj = self.eval(node.obj)
        index = self.eval(node.index)
        if isinstance(obj, list):
            idx = self._check_index(index, len(obj), 'list')
            return obj[idx]
        elif isinstance(obj, dict):
            if index in obj:
                return obj[index]
            return None
        elif isinstance(obj, str):
            idx = self._check_index(index, len(obj), 'string')
            return obj[idx]
        raise EvalError(
            "Cannot index this value",
            suggestion="Only lists, dictionaries and strings can be indexed"
        )

    def eval_IndexAssignment(self, node):
        obj = self.eval(node.obj)
        index = self.eval(node.index)
        value = self.eval(node.value)
        if isinstance(obj, list):
            idx = self._check_index(index, len(obj), 'list')
            obj[idx] = value
            return value
        elif isinstance(obj, dict):
            obj[index] = value
            return value
        raise EvalError("Cannot assign to an index of this value")

    def _check_index(self, index, length, kind):
        if not isinstance(index, int) or isinstance(index, bool):
            raise EvalError(f"{kind.capitalize()} index must be a whole number")
        if index < 0:
            index += length
        if index < 0 or index >= length:
            raise EvalError(
                f"{kind.capitalize()} index {index} out of range (length {length})"
            )
        return index

    # ── Control flow ──────────────────────────────────────────────────────────

    def eval_IfStmt(self, node):
        if self.is_truthy(self.eval(node.condition)):
            for stmt in node.consequent:
                self.eval(stmt)
        else:
            for cond, body in node.alternates:
                if self.is_truthy(self.eval(cond)):
                    for stmt in body:
                        self.eval(stmt)
                    return
            if node.else_body:
                for stmt in node.else_body:
                    self.eval(stmt)

    def eval_ForStmt(self, node):
        iterable = self.eval(node.iterable)
        if isinstance(iterable, (int, float)):
            iterable = range(int(iterable))
        if not hasattr(iterable, '__iter__'):
            raise EvalError(
                f"Cannot loop over {self.type_name(iterable)}",
                suggestion="'for' needs a list, string or range — try for x in range(10):"
            )
        try:
            for item in iterable:
                self.assign_name(node.variable, item)
                try:
                    for stmt in node.body:
                        self.eval(stmt)
                except ContinueException:
                    continue
                except BreakException:
                    break
        except BreakException:
            pass

    def eval_WhileStmt(self, node):
        iterations = 0
        try:
            while self.is_truthy(self.eval(node.condition)):
                try:
                    for stmt in node.body:
                        self.eval(stmt)
                except ContinueException:
                    continue
                except BreakException:
                    break
                iterations += 1
                if iterations > 50_000_000:
                    raise EvalError("while loop ran too long — possible infinite loop")
        except BreakException:
            pass

    def eval_RepeatStmt(self, node):
        count = self.eval(node.count)
        if not isinstance(count, (int, float)):
            raise EvalError("'repeat' needs a number of times")
        try:
            for _ in range(int(count)):
                try:
                    for stmt in node.body:
                        self.eval(stmt)
                except ContinueException:
                    continue
                except BreakException:
                    break
        except BreakException:
            pass

    def eval_SwitchStmt(self, node):
        subject = self.eval(node.subject)
        for case_values, body in node.cases:
            for value_node in case_values:
                if self.values_equal(subject, self.eval(value_node)):
                    for stmt in body:
                        self.eval(stmt)
                    return
        if node.default_body:
            for stmt in node.default_body:
                self.eval(stmt)

    def values_equal(self, a, b):
        return a == b

    def eval_TryCatch(self, node):
        try:
            for stmt in node.try_body:
                self.eval(stmt)
        except (ReturnException, BreakException, ContinueException):
            raise  # control flow must never be swallowed by catch
        except EppError as e:
            self.run_catch(node, str(e))
        except Exception as e:
            self.run_catch(node, f"{type(e).__name__}: {e}")

    def run_catch(self, node, message):
        if node.catch_var:
            self.assign_name(node.catch_var, message)
        if node.catch_body:
            for stmt in node.catch_body:
                self.eval(stmt)

    def eval_BreakStmt(self, node):
        raise BreakException()

    def eval_ContinueStmt(self, node):
        raise ContinueException()

    def eval_ReturnStmt(self, node):
        value = self.eval(node.value) if node.value else None
        raise ReturnException(value)

    def eval_ImportStmt(self, node):
        path = node.path.replace('\\', '/')
        candidates = [
            os.path.join(self.script_dir, path),
            path if os.path.isabs(path) else os.path.join(os.getcwd(), path),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), path),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib', path),
        ]
        import_path = next((c for c in candidates if os.path.isfile(c)), None)
        if import_path is None:
            raise EvalError(
                f"Cannot import '{path}': file not found",
                suggestion="Put the file in the same folder as your script"
            )
        import_path = os.path.abspath(import_path)
        if import_path in self.import_stack:
            raise EvalError(
                f"Circular import detected: '{os.path.basename(import_path)}' imports itself"
            )
        if import_path in self.imported_modules:
            return None  # each file executes only once
        with open(import_path, 'r') as f:
            source = f.read()
        self.imported_modules.add(import_path)
        saved_dir = self.script_dir
        self.script_dir = os.path.dirname(import_path)
        self.import_stack.append(import_path)
        try:
            self.run(source)
        finally:
            self.import_stack.pop()
            self.script_dir = saved_dir
        return None

    # ── Utilities ─────────────────────────────────────────────────────────────

    def type_name(self, value):
        if value is None:
            return 'null'
        if isinstance(value, bool):
            return 'bool'
        if isinstance(value, int):
            return 'int'
        if isinstance(value, float):
            return 'float'
        if isinstance(value, str):
            return 'string'
        if isinstance(value, list):
            return 'list'
        if isinstance(value, dict):
            return 'dict'
        if isinstance(value, Function):
            return 'function'
        return type(value).__name__

    def is_truthy(self, value):
        if value is None or value is False:
            return False
        if isinstance(value, (int, float)) and value == 0:
            return False
        if isinstance(value, str) and value == '':
            return False
        if isinstance(value, (list, dict)) and len(value) == 0:
            return False
        return True

    # ══ GUI Evaluator ═════════════════════════════════════════════════════════
    # Uses tkinter under the hood; the e++ user never sees it.

    def _tk(self):
        try:
            import tkinter as tk
            return tk
        except ImportError as e:
            raise EvalError(
                "GUI features need tkinter, which is not available on this system",
                suggestion="Install it with: sudo apt install python3-tk"
            )

    def _gui(self):
        """Return the shared GUI state dict, initialising on first call."""
        if not hasattr(self, '_gui_state'):
            self._gui_state = {
                'root': None,
                'widgets': {},   # id → tk widget
                'vars': {},      # id → tk var
                'images': [],    # keep image refs alive
                'timers': [],    # active after-job ids
            }
        return self._gui_state

    def _ensure_root(self):
        tk = self._tk()
        g = self._gui()
        if g['root'] is None:
            g['root'] = tk.Tk()
            g['root'].title("e++ App")
        return g['root']

    def _register_widget(self, widget_id, widget, var=None):
        g = self._gui()
        if widget_id:
            wid = str(widget_id)
            g['widgets'][wid] = widget
            if var is not None:
                g['vars'][wid] = var

    def eval_WindowStmt(self, node):
        root = self._ensure_root()
        title = str(self.eval(node.title))
        width = int(self.eval(node.width))
        height = int(self.eval(node.height))
        root.title(title)
        root.geometry(f"{width}x{height}")
        bg_color = str(self.eval(node.color)) if node.color else None
        if bg_color:
            root.configure(bg=bg_color)
        resizable = node.resizable
        if not isinstance(resizable, bool):
            resizable = self.is_truthy(self.eval(resizable))
        root.resizable(resizable, resizable)
        if node.widget_id:
            self._register_widget(str(self.eval(node.widget_id)), root)
        return None

    def _default_bg(self, root):
        return root.cget('bg') or 'white'

    def eval_LabelStmt(self, node):
        tk = self._tk()
        root = self._ensure_root()
        text = str(self.eval(node.text))
        x = int(self.eval(node.x))
        y = int(self.eval(node.y))
        font_size = int(self.eval(node.font_size)) if node.font_size else 12
        color = str(self.eval(node.color)) if node.color else None
        kwargs = {'text': text, 'font': ('Arial', font_size), 'bg': self._default_bg(root)}
        if color:
            kwargs['fg'] = color
        lbl = tk.Label(root, **kwargs)
        lbl.place(x=x, y=y)
        if node.widget_id:
            self._register_widget(self.eval(node.widget_id), lbl)
        return None

    def eval_ButtonStmt(self, node):
        tk = self._tk()
        root = self._ensure_root()
        text = str(self.eval(node.text))
        x = int(self.eval(node.x))
        y = int(self.eval(node.y))
        width = int(self.eval(node.width)) if node.width else None
        height = int(self.eval(node.height)) if node.height else None
        color = str(self.eval(node.color)) if node.color else None
        on_click = node.on_click  # function name string

        def _cmd():
            self.fire_handler(on_click)

        kwargs = {'text': text, 'command': _cmd}
        if width:
            kwargs['width'] = max(1, width // 8)   # tkinter uses char units
        if height:
            kwargs['height'] = max(1, height // 20)
        if color:
            kwargs['bg'] = color
        btn = tk.Button(root, **kwargs)
        btn.place(x=x, y=y)
        if node.widget_id:
            self._register_widget(self.eval(node.widget_id), btn)
        return None

    def fire_handler(self, handler_name, *args):
        """Call a named E++ function from a GUI event; errors go to stderr."""
        import sys
        if not handler_name:
            return
        found, scope = self.lookup(handler_name)
        if not found:
            raise EvalError(f"Function '{handler_name}' is not defined")
        fn = scope[handler_name]
        try:
            if isinstance(fn, Function):
                self.call_function(fn, list(args))
            elif callable(fn):
                fn(*args)
        except EppError as e:
            print(str(e), file=sys.stderr)
        except Exception as e:
            print(f"Unexpected error in '{handler_name}': {e}", file=sys.stderr)

    def eval_InputStmt(self, node):
        tk = self._tk()
        root = self._ensure_root()
        wid = str(self.eval(node.widget_id))
        x = int(self.eval(node.x))
        y = int(self.eval(node.y))
        width = int(self.eval(node.width)) if node.width else 200
        placeholder = str(self.eval(node.placeholder)) if node.placeholder else ''
        show = '*' if node.password else ''

        var = tk.StringVar()
        entry = tk.Entry(root, textvariable=var, width=max(1, width // 8), show=show)
        if placeholder:
            entry.insert(0, placeholder)
            entry.config(fg='grey')

            def _focus_in(e):
                if entry.get() == placeholder:
                    entry.delete(0, 'end')
                    entry.config(fg='black')

            def _focus_out(e):
                if entry.get() == '':
                    entry.insert(0, placeholder)
                    entry.config(fg='grey')
            entry.bind('<FocusIn>', _focus_in)
            entry.bind('<FocusOut>', _focus_out)
        entry.place(x=x, y=y)
        self._register_widget(wid, entry, var)
        return None

    def eval_ImageStmt(self, node):
        tk = self._tk()
        root = self._ensure_root()
        g = self._gui()
        path = str(self.eval(node.path))
        x = int(self.eval(node.x))
        y = int(self.eval(node.y))
        width = int(self.eval(node.width)) if node.width else None
        height = int(self.eval(node.height)) if node.height else None
        try:
            from PIL import Image, ImageTk
            img = Image.open(path)
            if width and height:
                img = img.resize((width, height))
            elif width:
                ratio = width / img.width
                img = img.resize((width, int(img.height * ratio)))
            elif height:
                ratio = height / img.height
                img = img.resize((int(img.width * ratio), height))
            tk_img = ImageTk.PhotoImage(img)
        except ImportError:
            tk_img = tk.PhotoImage(file=path)
            if width or height:
                factor_w = max(1, tk_img.width() // max(1, width or tk_img.width()))
                factor_h = max(1, tk_img.height() // max(1, height or tk_img.height()))
                try:
                    tk_img = tk_img.subsample(factor_w, factor_h)
                except Exception:
                    pass
        g['images'].append(tk_img)
        lbl = tk.Label(root, image=tk_img, bg=self._default_bg(root))
        lbl.place(x=x, y=y)
        return None

    def eval_TextboxStmt(self, node):
        tk = self._tk()
        root = self._ensure_root()
        wid = str(self.eval(node.widget_id))
        x = int(self.eval(node.x))
        y = int(self.eval(node.y))
        width = int(self.eval(node.width))
        height = int(self.eval(node.height))
        tb = tk.Text(root, width=max(1, width // 8), height=max(1, height // 20))
        tb.place(x=x, y=y)
        self._register_widget(wid, tb)
        return None

    def eval_CheckboxStmt(self, node):
        tk = self._tk()
        root = self._ensure_root()
        wid = str(self.eval(node.widget_id))
        text = str(self.eval(node.text)) if node.text else ''
        x = int(self.eval(node.x))
        y = int(self.eval(node.y))
        var = tk.BooleanVar()

        def _cmd():
            self.fire_handler(node.on_change)

        cb = tk.Checkbutton(root, text=text, variable=var,
                            command=_cmd if node.on_change else None,
                            bg=self._default_bg(root))
        cb.place(x=x, y=y)
        self._register_widget(wid, cb, var)
        return None

    def eval_DropdownStmt(self, node):
        tk = self._tk()
        from tkinter import ttk
        root = self._ensure_root()
        wid = str(self.eval(node.widget_id))
        options = self.eval(node.options)  # list
        x = int(self.eval(node.x))
        y = int(self.eval(node.y))
        if not isinstance(options, list):
            raise EvalError("'options' must be a list, e.g. options [\"a\", \"b\"]")
        var = tk.StringVar(value=str(options[0]) if options else '')

        def _cmd(event=None):
            self.fire_handler(node.on_change)

        combo = ttk.Combobox(root, textvariable=var,
                             values=[str(o) for o in options],
                             state='readonly')
        if node.on_change:
            combo.bind('<<ComboboxSelected>>', _cmd)
        combo.place(x=x, y=y)
        self._register_widget(wid, combo, var)
        return None

    def eval_SliderStmt(self, node):
        tk = self._tk()
        from tkinter import ttk
        root = self._ensure_root()
        wid = str(self.eval(node.widget_id))
        minimum = float(self.eval(node.minimum))
        maximum = float(self.eval(node.maximum))
        x = int(self.eval(node.x))
        y = int(self.eval(node.y))
        var = tk.DoubleVar(value=minimum)

        def _cmd(raw):
            self.fire_handler(node.on_change)

        slider = ttk.Scale(root, from_=minimum, to=maximum,
                           variable=var, orient='horizontal', length=180,
                           command=_cmd if node.on_change else None)
        slider.place(x=x, y=y)
        self._register_widget(wid, slider, var)
        return None

    def eval_ProgressStmt(self, node):
        tk = self._tk()
        from tkinter import ttk
        root = self._ensure_root()
        wid = str(self.eval(node.widget_id))
        x = int(self.eval(node.x))
        y = int(self.eval(node.y))
        width = int(self.eval(node.width)) if node.width else 200
        var = tk.DoubleVar(value=0)
        bar = ttk.Progressbar(root, maximum=100, variable=var,
                              length=max(40, width), mode='determinate')
        bar.place(x=x, y=y)
        self._register_widget(wid, bar, var)
        return None

    def eval_SetProgressStmt(self, node):
        g = self._gui()
        wid = str(self.eval(node.widget_id))
        value = self.eval(node.value)
        if wid in g['vars']:
            g['vars'][wid].set(float(value))
        elif wid in g['widgets']:
            g['widgets'][wid]['value'] = float(value)
        else:
            raise EvalError(f"Widget '{wid}' not found — did you define it?")
        return None

    def eval_CanvasStmt(self, node):
        tk = self._tk()
        root = self._ensure_root()
        wid = str(self.eval(node.widget_id))
        width = int(self.eval(node.width))
        height = int(self.eval(node.height))
        color = str(self.eval(node.color)) if node.color else 'white'
        canvas = tk.Canvas(root, width=width, height=height, bg=color,
                           highlightthickness=0)
        canvas.place(x=20, y=20)
        self._register_widget(wid, canvas)
        return None

    def eval_DrawStmt(self, node):
        g = self._gui()
        cid = str(self.eval(node.canvas_id))
        if cid not in g['widgets']:
            raise EvalError(f"Canvas '{cid}' not found — create it with: canvas \"{cid}\" ...")
        canvas = g['widgets'][cid]
        coords = [float(self.eval(c)) for c in node.coords]
        color = str(self.eval(node.color)) if node.color else 'black'
        fill = str(self.eval(node.fill)) if node.fill else None
        outline_width = int(self.eval(node.outline_width)) if node.outline_width else 2

        shape = node.shape
        if shape == 'line':
            canvas.create_line(*coords[:4], fill=color, width=outline_width)
        elif shape == 'rectangle':
            canvas.create_rectangle(coords[0], coords[1], coords[2], coords[3],
                                    outline=color, fill=fill or '',
                                    width=outline_width)
        elif shape in ('circle', 'dot'):
            cx, cy = coords[0], coords[1]
            r = coords[2] if len(coords) > 2 else 10
            if shape == 'dot':
                r = max(1.5, r / 5)
            canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                               outline=color, fill=fill or (color if shape == 'dot' else ''),
                               width=outline_width)
        elif shape == 'text':
            txt = str(self.eval(node.text)) if node.text else ''
            canvas.create_text(coords[0], coords[1], text=txt,
                               fill=color, font=('Arial', 14), anchor='w')
        else:
            raise EvalError(f"I don't know how to draw '{shape}'")
        return None

    def eval_ClearCanvasStmt(self, node):
        g = self._gui()
        cid = str(self.eval(node.canvas_id))
        if cid in g['widgets']:
            g['widgets'][cid].delete('all')
        else:
            raise EvalError(f"Canvas '{cid}' not found")
        return None

    def eval_TimerStmt(self, node):
        root = self._ensure_root()
        interval = float(self.eval(node.interval))
        ms = int(interval * 1000) if node.in_seconds else int(interval)

        def tick():
            self.fire_handler(node.handler)
            job = root.after(ms, tick)
            g = self._gui()
            g['timers'].append(job)

        job = root.after(ms, tick)
        self._gui()['timers'].append(job)
        return None

    def eval_AfterStmt(self, node):
        root = self._ensure_root()
        delay = float(self.eval(node.delay))
        ms = int(delay * 1000) if node.in_seconds else int(delay)
        job = root.after(ms, lambda: self.fire_handler(node.handler))
        self._gui()['timers'].append(job)
        return None

    def eval_BeepStmt(self, node):
        freq = int(self.eval(node.frequency)) if node.frequency else 880
        duration_ms = int(self.eval(node.duration)) if node.duration else 150
        g = self._gui()
        if g['root'] is not None:
            try:
                import sys as _sys
                if _sys.platform == 'win32':
                    import winsound
                    winsound.Beep(freq, duration_ms)
                else:
                    g['root'].bell()
            except Exception:
                print('\a', end='', flush=True)
        else:
            print('\a', end='', flush=True)
        return None

    def eval_SetTextStmt(self, node):
        g = self._gui()
        wid = str(self.eval(node.widget_id))
        value = self.to_display_string(self.eval(node.value))
        if wid in g['vars']:
            current = g['vars'][wid].get()
            if isinstance(current, bool):
                g['vars'][wid].set(self.is_truthy(value))
            else:
                try:
                    g['vars'][wid].set(type(current)(value))
                except (ValueError, TypeError):
                    g['vars'][wid].set(value)
        elif wid in g['widgets']:
            w = g['widgets'][wid]
            if hasattr(w, 'config'):
                try:
                    w.config(text=value)
                except Exception:
                    try:
                        w.delete('1.0', 'end')
                        w.insert('1.0', value)
                    except Exception:
                        pass
        else:
            raise EvalError(f"Widget '{wid}' not found — did you define it?")
        return None

    def eval_GetTextStmt(self, node):
        g = self._gui()
        wid = str(self.eval(node.widget_id))
        if wid in g['vars']:
            return g['vars'][wid].get()
        if wid in g['widgets']:
            w = g['widgets'][wid]
            tk = self._tk()
            if isinstance(w, tk.Text):
                return w.get('1.0', 'end').rstrip('\n')
            if isinstance(w, tk.Tk):
                return w.title()
            if hasattr(w, 'get'):
                return w.get()
            if hasattr(w, 'cget'):
                try:
                    return w.cget('text')
                except Exception:
                    return ''
        raise EvalError(f"Widget '{wid}' not found")

    def eval_ShowWindowStmt(self, node):
        g = self._gui()
        if g['root'] is None:
            raise EvalError(
                "No window created — use 'window' before 'show_window'",
                suggestion="Add something like: window \"My App\" width 400 height 300"
            )
        g['root'].mainloop()
        return None

    def eval_AlertStmt(self, node):
        from tkinter import messagebox
        self._ensure_root()
        msg = self.to_display_string(self.eval(node.message))
        messagebox.showinfo("Alert", msg)
        return None

    def eval_SetColorStmt(self, node):
        g = self._gui()
        wid = str(self.eval(node.widget_id))
        color = str(self.eval(node.color))
        if wid in g['widgets']:
            w = g['widgets'][wid]
            try:
                w.config(bg=color)
            except Exception:
                try:
                    w.config(foreground=color)
                except Exception:
                    raise EvalError(f"Cannot set color of widget '{wid}' to '{color}'")
        else:
            raise EvalError(f"Widget '{wid}' not found")
        return None

    def eval_SetVisibleStmt(self, node):
        g = self._gui()
        wid = str(self.eval(node.widget_id))
        visible = self.is_truthy(self.eval(node.visible))
        if wid in g['widgets']:
            w = g['widgets'][wid]
            if visible:
                w.place_configure()
                w.lift()
            else:
                w.place_forget()
        else:
            raise EvalError(f"Widget '{wid}' not found")
        return None
