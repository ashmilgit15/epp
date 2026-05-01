import os
import sys
import math
import random as rnd
import time
from interpreter.nodes import *
from interpreter.errors import EvalError, ReturnException

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
    def __init__(self, name, params, body, closure=None):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure or {}

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
        self.output = []
        self.import_stack = []
        if stdlib:
            self.register_stdlib(stdlib)

    def register_stdlib(self, stdlib):
        for name, func in stdlib.items():
            self.global_scope[name] = func

    def eval(self, node):
        method_name = f'eval_{type(node).__name__}'
        method = getattr(self, method_name, None)
        if method is None:
            raise EvalError(f"No evaluator for {type(node).__name__}")
        return method(node)

    def eval_Program(self, node):
        result = None
        for stmt in node.statements:
            result = self.eval(stmt)
        return result

    def eval_SayStmt(self, node):
        value = self.eval(node.expr)
        self.output.append(str(value))
        print(str(value))
        return None

    def eval_ExpressionStatement(self, node):
        return self.eval(node.expr)

    def eval_Number(self, node):
        return node.value

    def eval_String(self, node):
        return node.value

    def eval_Boolean(self, node):
        return node.value

    def eval_Null(self, node):
        return None

    def eval_Identifier(self, node):
        name = node.name
        if name in self.global_scope:
            return self.global_scope[name]
        raise EvalError(f"'{name}' is not defined", suggestion="Did you forget to assign it?")

    def eval_ListLiteral(self, node):
        return [self.eval(e) for e in node.elements]

    def eval_DictLiteral(self, node):
        result = {}
        for k, v in node.pairs:
            key = self.eval(k)
            val = self.eval(v)
            result[key] = val
        return result

    def eval_Assignment(self, node):
        value = self.eval(node.value)
        self.global_scope[node.name] = value
        return value

    def eval_BinaryOp(self, node):
        left = self.eval(node.left)
        right = self.eval(node.right)
        if node.operator == '+':
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)
            return left + right
        elif node.operator == '-':
            return left - right
        elif node.operator == '*':
            return left * right
        elif node.operator == '/':
            if right == 0:
                raise EvalError("Cannot divide by zero")
            return left / right
        raise EvalError(f"Unknown operator '{node.operator}'")

    def eval_UnaryOp(self, node):
        operand = self.eval(node.operand)
        if node.operator == 'not':
            return not self.is_truthy(operand)
        if node.operator == '-':
            return -operand
        raise EvalError(f"Unknown unary operator '{node.operator}'")

    def eval_Comparison(self, node):
        left = self.eval(node.left)
        right = self.eval(node.right)
        op = node.operator
        if op == 'is':
            return left == right
        elif op == 'is not':
            return left != right
        elif op == 'is greater than':
            return left > right
        elif op == 'is less than':
            return left < right
        elif op == 'is equal to':
            return left == right
        elif op == 'is greater than or equal to':
            return left >= right
        elif op == 'is less than or equal to':
            return left <= right
        raise EvalError(f"Unknown comparison '{op}'")

    def eval_LogicalOp(self, node):
        left = self.eval(node.left)
        if node.operator == 'and':
            return self.is_truthy(left) and self.is_truthy(self.eval(node.right))
        elif node.operator == 'or':
            return self.is_truthy(left) or self.is_truthy(self.eval(node.right))
        raise EvalError(f"Unknown logical operator '{node.operator}'")

    def eval_FuncCall(self, node):
        name = node.name
        args = [self.eval(arg) for arg in node.args]
        if name in self.global_scope:
            func = self.global_scope[name]
            if isinstance(func, Function):
                return self.call_function(func, args)
            elif isinstance(func, Class):
                return self.instantiate_class(func, args)
            if callable(func) and not isinstance(func, type):
                if hasattr(func, '_epp_native'):
                    return func(self, args)
                return func(*args)
            raise EvalError(f"'{name}' is not a function")
        raise EvalError(f"'{name}' is not defined", suggestion="Did you define it with 'func'?")

    def call_function(self, func, args):
        if len(args) != len(func.params):
            raise EvalError(f"'{func.name}' expects {len(func.params)} argument(s), got {len(args)}")
        local_scope = dict(func.closure)
        local_scope[func.name] = func
        for param, arg in zip(func.params, args):
            local_scope[param] = arg
        old_scope = self.global_scope
        self.global_scope = local_scope
        try:
            result = None
            for stmt in func.body:
                self.eval(stmt)
            return result
        except ReturnException as e:
            result = e.value
        finally:
            self.global_scope = old_scope
        return result

    def eval_FuncDef(self, node):
        func = Function(node.name, node.params, node.body, self.global_scope.copy())
        self.global_scope[node.name] = func
        return None

    def instantiate_class(self, cls, args):
        instance = EppInstance(cls)
        if hasattr(cls, 'init'):
            init_method = getattr(cls, 'init')
            if isinstance(init_method, Function):
                old_scope = self.global_scope
                new_scope = instance.fields.copy()
                new_scope['self'] = instance
                if len(args) == len(init_method.params):
                    for param, arg in zip(init_method.params, args):
                        new_scope[param] = arg
                self.global_scope = new_scope
                try:
                    for stmt in init_method.body:
                        self.eval(stmt)
                except ReturnException:
                    pass
                finally:
                    self.global_scope = old_scope
        return instance

    def eval_ClassDef(self, node):
        cls = Class(node.name, node.body)
        for stmt in node.body:
            if isinstance(stmt, FuncDef):
                method = Function(stmt.name, stmt.params, stmt.body, self.global_scope.copy())
                setattr(cls, stmt.name, method)
        self.global_scope[node.name] = cls
        return None

    def eval_MethodCall(self, node):
        obj = self.eval(node.obj)
        method_name = node.method
        args = [self.eval(arg) for arg in node.args]
        if isinstance(obj, EppInstance):
            if method_name in obj.fields:
                method = obj.fields[method_name]
            elif hasattr(obj.cls, method_name):
                method = getattr(obj.cls, method_name)
            else:
                raise EvalError(f"'{method_name}' is not defined in class '{obj.cls.name}'")
            if isinstance(method, Function):
                old_scope = self.global_scope
                self.global_scope = obj.fields.copy()
                self.global_scope['self'] = obj
                try:
                    result = None
                    for stmt in method.body:
                        self.eval(stmt)
                except ReturnException as e:
                    result = e.value
                finally:
                    self.global_scope = old_scope
                return result
            return method(*args)
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
        elif method == 'len' or method == 'length':
            return len(lst)
        raise EvalError(f"List has no method '{method}'")

    def handle_string_method(self, s, method, args):
        if method == 'len' or method == 'length':
            return len(s)
        raise EvalError(f"String has no method '{method}'")

    def handle_dict_method(self, d, method, args):
        if method == 'len' or method == 'length':
            return len(d)
        elif method == 'keys':
            return list(d.keys())
        elif method == 'values':
            return list(d.values())
        raise EvalError(f"Dict has no method '{method}'")

    def eval_MemberAccess(self, node):
        obj = self.eval(node.obj)
        member = node.member
        if isinstance(obj, EppInstance):
            return obj.get(member)
        elif isinstance(obj, dict):
            return obj.get(member)
        elif isinstance(obj, list):
            if member == 'len':
                return len(obj)
            raise EvalError(f"List has no member '{member}'")
        elif isinstance(obj, str):
            if member == 'len':
                return len(obj)
            raise EvalError(f"String has no member '{member}'")
        raise EvalError(f"Cannot access '{member}' of this value")

    def eval_PropertyAssignment(self, node):
        obj = self.eval(node.obj)
        value = self.eval(node.value)
        if isinstance(obj, EppInstance):
            obj.set(node.member, value)
        elif isinstance(obj, dict):
            obj[node.member] = value
        else:
            raise EvalError(f"Cannot set property '{node.member}' on this value")
        return value

    def eval_IndexAccess(self, node):
        obj = self.eval(node.obj)
        index = self.eval(node.index)
        if isinstance(obj, list):
            if not isinstance(index, int):
                raise EvalError(f"List index must be an integer")
            if index < 0 or index >= len(obj):
                raise EvalError(f"List index {index} out of range")
            return obj[index]
        elif isinstance(obj, dict):
            return obj.get(index)
        elif isinstance(obj, str):
            if not isinstance(index, int):
                raise EvalError(f"String index must be an integer")
            if index < 0 or index >= len(obj):
                raise EvalError(f"String index {index} out of range")
            return obj[index]
        raise EvalError(f"Cannot index this value")

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
        if hasattr(iterable, '__iter__'):
            old_val = self.global_scope.get(node.variable)
            for item in iterable:
                self.global_scope[node.variable] = item
                for stmt in node.body:
                    self.eval(stmt)
            if old_val is not None:
                self.global_scope[node.variable] = old_val
            elif node.variable in self.global_scope:
                del self.global_scope[node.variable]

    def eval_WhileStmt(self, node):
        while self.is_truthy(self.eval(node.condition)):
            for stmt in node.body:
                self.eval(stmt)

    def eval_TryCatch(self, node):
        try:
            for stmt in node.try_body:
                self.eval(stmt)
        except Exception as e:
            if node.catch_var:
                self.global_scope[node.catch_var] = str(e)
            for stmt in node.catch_body:
                self.eval(stmt)

    def eval_ReturnStmt(self, node):
        value = self.eval(node.value) if node.value else None
        raise ReturnException(value)

    def eval_ImportStmt(self, node):
        path = node.path
        import_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
        if not os.path.exists(import_path):
            lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib', path)
            if os.path.exists(lib_path):
                import_path = lib_path
        if not os.path.exists(import_path):
            raise EvalError(f"Cannot import '{path}': file not found")
        with open(import_path, 'r') as f:
            source = f.read()
        from interpreter.lexer import Lexer
        from interpreter.parser import Parser
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        for stmt in program.statements:
            self.eval(stmt)

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

    def run(self, source):
        from interpreter.lexer import Lexer
        from interpreter.parser import Parser
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        return self.eval(program)

    # ── GUI Evaluator ─────────────────────────────────────────────────────────
    # Uses tkinter under the hood; the e++ user never sees it.

    def _gui(self):
        """Return the shared GUI state dict, initialising on first call."""
        if not hasattr(self, '_gui_state'):
            self._gui_state = {
                'root': None,
                'widgets': {},   # id → tk widget
                'vars': {},      # id → tk.StringVar / tk.BooleanVar
                'images': [],    # keep PIL/tk image refs alive
            }
        return self._gui_state

    def _ensure_root(self):
        import tkinter as tk
        g = self._gui()
        if g['root'] is None:
            g['root'] = tk.Tk()
            g['root'].title("e++ App")
        return g['root']

    def eval_WindowStmt(self, node):
        import tkinter as tk
        root = self._ensure_root()
        title  = self.eval(node.title)
        width  = int(self.eval(node.width))  if not isinstance(node.width,  int) else node.width
        height = int(self.eval(node.height)) if not isinstance(node.height, int) else node.height
        root.title(str(title))
        root.geometry(f"{width}x{height}")
        if node.color:
            root.configure(bg=str(self.eval(node.color)))
        resizable = node.resizable
        if not isinstance(resizable, bool):
            resizable = self.is_truthy(self.eval(resizable))
        root.resizable(resizable, resizable)
        return None

    def eval_LabelStmt(self, node):
        import tkinter as tk
        root = self._ensure_root()
        g = self._gui()
        text      = str(self.eval(node.text))
        x         = int(self.eval(node.x))
        y         = int(self.eval(node.y))
        font_size = int(self.eval(node.font_size)) if node.font_size else 12
        color     = str(self.eval(node.color)) if node.color else None
        bg        = root.cget('bg') or 'white'
        kwargs = {'text': text, 'font': ('Arial', font_size), 'bg': bg}
        if color:
            kwargs['fg'] = color
        lbl = tk.Label(root, **kwargs)
        lbl.place(x=x, y=y)
        if node.widget_id:
            wid = str(self.eval(node.widget_id))
            g['widgets'][wid] = lbl
        return None

    def eval_ButtonStmt(self, node):
        import tkinter as tk
        root = self._ensure_root()
        g = self._gui()
        text     = str(self.eval(node.text))
        x        = int(self.eval(node.x))
        y        = int(self.eval(node.y))
        width    = int(self.eval(node.width))  if node.width  else None
        height   = int(self.eval(node.height)) if node.height else None
        color    = str(self.eval(node.color))  if node.color  else None
        on_click = node.on_click  # function name string

        def _cmd():
            if on_click and on_click in self.global_scope:
                fn = self.global_scope[on_click]
                self.call_function(fn, [])
            elif on_click:
                raise EvalError(f"Function '{on_click}' is not defined")

        kwargs = {'text': text, 'command': _cmd}
        if width:  kwargs['width']  = width  // 8   # tkinter uses char units
        if height: kwargs['height'] = height // 20
        if color:  kwargs['bg']     = color
        btn = tk.Button(root, **kwargs)
        btn.place(x=x, y=y)
        if node.widget_id:
            wid = str(self.eval(node.widget_id))
            g['widgets'][wid] = btn
        return None

    def eval_InputStmt(self, node):
        import tkinter as tk
        root = self._ensure_root()
        g = self._gui()
        wid         = str(self.eval(node.widget_id))
        x           = int(self.eval(node.x))
        y           = int(self.eval(node.y))
        width       = int(self.eval(node.width)) if node.width else 200
        placeholder = str(self.eval(node.placeholder)) if node.placeholder else ''
        show        = '*' if node.password else ''

        var = tk.StringVar()
        g['vars'][wid] = var

        entry = tk.Entry(root, textvariable=var, width=width // 8, show=show)
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
            entry.bind('<FocusIn>',  _focus_in)
            entry.bind('<FocusOut>', _focus_out)
        entry.place(x=x, y=y)
        g['widgets'][wid] = entry
        return None

    def eval_ImageStmt(self, node):
        import tkinter as tk
        root = self._ensure_root()
        g = self._gui()
        path   = str(self.eval(node.path))
        x      = int(self.eval(node.x))
        y      = int(self.eval(node.y))
        width  = int(self.eval(node.width))  if node.width  else None
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
            # Pillow not available — use tkinter PhotoImage (PNG/GIF only)
            tk_img = tk.PhotoImage(file=path)
            if width or height:
                pass  # subsample/zoom not applied if no PIL
        g['images'].append(tk_img)
        lbl = tk.Label(root, image=tk_img, bg=root.cget('bg') or 'white')
        lbl.place(x=x, y=y)
        if node.widget_id if hasattr(node, 'widget_id') else False:
            wid = str(self.eval(node.widget_id))
            g['widgets'][wid] = lbl
        return None

    def eval_TextboxStmt(self, node):
        import tkinter as tk
        root = self._ensure_root()
        g = self._gui()
        wid    = str(self.eval(node.widget_id))
        x      = int(self.eval(node.x))
        y      = int(self.eval(node.y))
        width  = int(self.eval(node.width))
        height = int(self.eval(node.height))
        tb = tk.Text(root, width=width // 8, height=height // 20)
        tb.place(x=x, y=y)
        g['widgets'][wid] = tb
        return None

    def eval_CheckboxStmt(self, node):
        import tkinter as tk
        root = self._ensure_root()
        g = self._gui()
        wid  = str(self.eval(node.widget_id))
        text = str(self.eval(node.text)) if node.text else ''
        x    = int(self.eval(node.x))
        y    = int(self.eval(node.y))
        var  = tk.BooleanVar()
        g['vars'][wid] = var

        def _cmd():
            if node.on_change and node.on_change in self.global_scope:
                fn = self.global_scope[node.on_change]
                self.call_function(fn, [])

        cb = tk.Checkbutton(root, text=text, variable=var,
                            command=_cmd if node.on_change else None,
                            bg=root.cget('bg') or 'white')
        cb.place(x=x, y=y)
        g['widgets'][wid] = cb
        return None

    def eval_DropdownStmt(self, node):
        import tkinter as tk
        from tkinter import ttk
        root = self._ensure_root()
        g = self._gui()
        wid     = str(self.eval(node.widget_id))
        options = self.eval(node.options)  # list
        x       = int(self.eval(node.x))
        y       = int(self.eval(node.y))
        var = tk.StringVar(value=options[0] if options else '')
        g['vars'][wid] = var

        def _cmd(event=None):
            if node.on_change and node.on_change in self.global_scope:
                fn = self.global_scope[node.on_change]
                self.call_function(fn, [])

        combo = ttk.Combobox(root, textvariable=var,
                             values=[str(o) for o in options],
                             state='readonly')
        if node.on_change:
            combo.bind('<<ComboboxSelected>>', _cmd)
        combo.place(x=x, y=y)
        g['widgets'][wid] = combo
        return None

    def eval_SetTextStmt(self, node):
        g = self._gui()
        wid   = str(self.eval(node.widget_id))
        value = str(self.eval(node.value))
        import tkinter as tk
        if wid in g['vars']:
            g['vars'][wid].set(value)
        elif wid in g['widgets']:
            w = g['widgets'][wid]
            if hasattr(w, 'config'):
                try:
                    w.config(text=value)
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
            import tkinter as tk
            if isinstance(w, tk.Text):
                return w.get('1.0', 'end').rstrip('\n')
            if hasattr(w, 'get'):
                return w.get()
            if hasattr(w, 'cget'):
                return w.cget('text')
        raise EvalError(f"Widget '{wid}' not found")

    def eval_ShowWindowStmt(self, node):
        g = self._gui()
        if g['root'] is None:
            raise EvalError("No window created — use 'window' before 'show_window'")
        g['root'].mainloop()
        return None

    def eval_AlertStmt(self, node):
        from tkinter import messagebox
        self._ensure_root()
        msg = str(self.eval(node.message))
        messagebox.showinfo("Alert", msg)
        return None

    def eval_SetColorStmt(self, node):
        g = self._gui()
        wid   = str(self.eval(node.widget_id))
        color = str(self.eval(node.color))
        if wid in g['widgets']:
            w = g['widgets'][wid]
            try:
                w.config(bg=color)
            except Exception:
                try:
                    w.config(foreground=color)
                except Exception:
                    pass
        else:
            raise EvalError(f"Widget '{wid}' not found")
        return None

    def eval_SetVisibleStmt(self, node):
        g = self._gui()
        wid     = str(self.eval(node.widget_id))
        visible = self.is_truthy(self.eval(node.visible))
        if wid in g['widgets']:
            w = g['widgets'][wid]
            if visible:
                w.place_configure()  # restore last placement
                w.lift()
            else:
                w.place_forget()
        else:
            raise EvalError(f"Widget '{wid}' not found")
        return None