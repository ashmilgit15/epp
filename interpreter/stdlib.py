import os
import sys
import math
import random
import time
from interpreter.errors import EvalError

def make_stdlib(evaluator):
    def epp_say(args):
        output = ' '.join(str(arg) for arg in args)
        evaluator.output.append(output)
        print(output)

    def epp_input(args):
        prompt = args[0] if args else ''
        try:
            return input(prompt)
        except EOFError:
            return ''

    def epp_type(args):
        val = args[0] if args else None
        if val is None: return 'null'
        if isinstance(val, bool): return 'bool'
        if isinstance(val, int): return 'int'
        if isinstance(val, float): return 'float'
        if isinstance(val, str): return 'string'
        if isinstance(val, list): return 'list'
        if isinstance(val, dict): return 'dict'
        return 'unknown'

    def epp_len(args):
        val = args[0] if args else None
        if isinstance(val, (list, str, dict)):
            return len(val)
        raise EvalError(f"'len' is not defined for '{type(val).__name__}'")

    def epp_range(args):
        n = args[0] if args else 0
        return list(range(int(n)))

    def epp_push(args):
        lst = args[0] if args else None
        item = args[1] if len(args) > 1 else None
        if not isinstance(lst, list):
            raise EvalError(f"'push' requires a list")
        lst.append(item)
        return None

    def epp_pop(args):
        lst = args[0] if args else None
        if not isinstance(lst, list):
            raise EvalError(f"'pop' requires a list")
        if len(lst) == 0:
            return None
        return lst.pop()

    def epp_keys(args):
        d = args[0] if args else None
        if not isinstance(d, dict):
            raise EvalError(f"'keys' requires a dictionary")
        return list(d.keys())

    def epp_values(args):
        d = args[0] if args else None
        if not isinstance(d, dict):
            raise EvalError(f"'values' requires a dictionary")
        return list(d.values())

    def epp_int(args):
        val = args[0] if args else 0
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return 0

    def epp_float(args):
        val = args[0] if args else 0
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    def epp_str(args):
        val = args[0] if args else ''
        return str(val)

    def epp_bool(args):
        val = args[0] if args else False
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)) and val == 0:
            return False
        if isinstance(val, str) and val == '':
            return False
        if isinstance(val, (list, dict)) and len(val) == 0:
            return False
        return bool(val)

    def epp_split(args):
        s = args[0] if args else ''
        delim = args[1] if len(args) > 1 else ' '
        return s.split(delim)

    def epp_join(args):
        lst = args[0] if args else []
        delim = args[1] if len(args) > 1 else ''
        return delim.join(str(item) for item in lst)

    def epp_trim(args):
        s = args[0] if args else ''
        return s.strip()

    def epp_replace(args):
        s = args[0] if args else ''
        old = args[1] if len(args) > 1 else ''
        new = args[2] if len(args) > 2 else ''
        return s.replace(old, new)

    def epp_read_file(args):
        path = args[0] if args else ''
        try:
            with open(path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            raise EvalError(f"File '{path}' not found")
        except IOError as e:
            raise EvalError(f"Cannot read file '{path}': {e}")

    def epp_write_file(args):
        path = args[0] if args else ''
        content = args[1] if len(args) > 1 else ''
        try:
            with open(path, 'w') as f:
                f.write(str(content))
        except IOError as e:
            raise EvalError(f"Cannot write file '{path}': {e}")
        return None

    def epp_append_file(args):
        path = args[0] if args else ''
        content = args[1] if len(args) > 1 else ''
        try:
            with open(path, 'a') as f:
                f.write(str(content))
        except IOError as e:
            raise EvalError(f"Cannot append to file '{path}': {e}")
        return None

    def epp_exists(args):
        path = args[0] if args else ''
        return os.path.exists(path)

    def epp_delete_file(args):
        path = args[0] if args else ''
        try:
            os.remove(path)
        except FileNotFoundError:
            raise EvalError(f"File '{path}' not found")
        except IOError as e:
            raise EvalError(f"Cannot delete file '{path}': {e}")
        return None

    def epp_random(args):
        return random.random()

    def epp_time(args):
        return time.time()

    def epp_sleep(args):
        seconds = args[0] if args else 1
        try:
            time.sleep(float(seconds))
        except ValueError:
            raise EvalError(f"'sleep' requires a number")
        return None

    def epp_abs(args):
        val = args[0] if args else 0
        return abs(val)

    def epp_min(args):
        vals = args[0] if args else []
        if not isinstance(vals, list) or len(vals) == 0:
            raise EvalError(f"'min' requires a non-empty list")
        return min(vals)

    def epp_max(args):
        vals = args[0] if args else []
        if not isinstance(vals, list) or len(vals) == 0:
            raise EvalError(f"'max' requires a non-empty list")
        return max(vals)

    def epp_sqrt(args):
        val = args[0] if args else 0
        return math.sqrt(val)

    def epp_fetch(args):
        url = args[0] if args else ''
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            raise EvalError(f"Cannot fetch '{url}': {e}")

    def epp_parse_json(args):
        import json
        text = args[0] if args else ''
        try:
            return json.loads(text)
        except Exception as e:
            raise EvalError(f"Cannot parse JSON: {e}")

    stdlib = {
        'say': lambda ev, args: epp_say(args),
        'input': lambda ev, args: epp_input(args),
        'type': lambda ev, args: epp_type(args),
        'len': lambda ev, args: epp_len(args),
        'range': lambda ev, args: epp_range(args),
        'push': lambda ev, args: epp_push(args),
        'pop': lambda ev, args: epp_pop(args),
        'keys': lambda ev, args: epp_keys(args),
        'values': lambda ev, args: epp_values(args),
        'int': lambda ev, args: epp_int(args),
        'float': lambda ev, args: epp_float(args),
        'str': lambda ev, args: epp_str(args),
        'bool': lambda ev, args: epp_bool(args),
        'split': lambda ev, args: epp_split(args),
        'join': lambda ev, args: epp_join(args),
        'trim': lambda ev, args: epp_trim(args),
        'replace': lambda ev, args: epp_replace(args),
        'read_file': lambda ev, args: epp_read_file(args),
        'write_file': lambda ev, args: epp_write_file(args),
        'append_file': lambda ev, args: epp_append_file(args),
        'exists': lambda ev, args: epp_exists(args),
        'delete_file': lambda ev, args: epp_delete_file(args),
        'random': lambda ev, args: epp_random(args),
        'time': lambda ev, args: epp_time(args),
        'sleep': lambda ev, args: epp_sleep(args),
        'abs': lambda ev, args: epp_abs(args),
        'min': lambda ev, args: epp_min(args),
        'max': lambda ev, args: epp_max(args),
        'sqrt': lambda ev, args: epp_sqrt(args),
        'fetch': lambda ev, args: epp_fetch(args),
        'parse_json': lambda ev, args: epp_parse_json(args),
    }
    for name, func in stdlib.items():
        func._epp_native = True
    return stdlib