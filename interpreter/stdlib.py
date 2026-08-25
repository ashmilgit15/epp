import os
import math
import random
import time
from interpreter.errors import EvalError


def make_stdlib(evaluator):
    def epp_say(args):
        output = ' '.join(evaluator.to_display_string(arg) for arg in args)
        evaluator.output.append(output)
        print(output)

    def epp_input(args):
        prompt = args[0] if args else ''
        try:
            return input(evaluator.to_display_string(prompt))
        except EOFError:
            raise EvalError(
                "input() reached the end of the input",
                suggestion="If you are piping data into your program, make sure there "
                           "are enough lines for every input() call"
            )

    def epp_type(args):
        val = args[0] if args else None
        return evaluator.type_name(val)

    def epp_len(args):
        val = args[0] if args else None
        if isinstance(val, (list, str, dict)):
            return len(val)
        raise EvalError(f"'len' is not defined for '{evaluator.type_name(val)}'")

    def epp_range(args):
        if not args:
            return []
        n = int(args[0])
        start, stop, step = 0, n, 1
        if len(args) >= 2:
            start, stop = int(args[0]), int(args[1])
        if len(args) >= 3:
            step = int(args[2])
        return list(range(start, stop, step))

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
        index = -1
        if len(args) > 1 and isinstance(args[1], (int, float)):
            index = int(args[1])
        if abs(index) >= len(lst):
            raise EvalError("Cannot pop from an empty spot — index out of range")
        return lst.pop(index)

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

    def _to_num(val, default=0):
        try:
            if isinstance(val, bool):
                return int(val)
            return float(val) if isinstance(val, str) and '.' in val else int(float(val))
        except (ValueError, TypeError):
            return default

    def epp_int(args):
        val = args[0] if args else 0
        try:
            if isinstance(val, float):
                return int(val)
            return int(str(val).strip())
        except (ValueError, TypeError):
            return 0

    def epp_float(args):
        val = args[0] if args else 0
        try:
            return float(str(val).strip())
        except (ValueError, TypeError):
            return 0.0

    def epp_str(args):
        val = args[0] if args else ''
        return evaluator.to_display_string(val)

    def epp_bool(args):
        return evaluator.is_truthy(args[0] if args else False)

    def epp_split(args):
        s = args[0] if args else ''
        delim = args[1] if len(args) > 1 else ' '
        return str(s).split(str(delim))

    def epp_join(args):
        lst = args[0] if args else []
        delim = args[1] if len(args) > 1 else ''
        if not isinstance(lst, list):
            raise EvalError("'join' requires a list")
        return str(delim).join(evaluator.to_display_string(item) for item in lst)

    def epp_trim(args):
        s = args[0] if args else ''
        return str(s).strip()

    def epp_replace(args):
        s = args[0] if args else ''
        old = args[1] if len(args) > 1 else ''
        new = args[2] if len(args) > 2 else ''
        return str(s).replace(str(old), str(new))

    def epp_upper(args):
        return str(args[0] if args else '').upper()

    def epp_lower(args):
        return str(args[0] if args else '').lower()

    def epp_contains(args):
        container = args[0] if args else None
        item = args[1] if len(args) > 1 else None
        if isinstance(container, (list, dict, str)):
            return item in container
        raise EvalError("'contains' requires a list, string or dictionary")

    def epp_index_of(args):
        lst = args[0] if args else None
        item = args[1] if len(args) > 1 else None
        if isinstance(lst, list):
            return lst.index(item) if item in lst else -1
        if isinstance(lst, str):
            return lst.find(str(item))
        raise EvalError("'index_of' requires a list or string")

    def epp_sort(args):
        lst = args[0] if args else []
        if not isinstance(lst, list):
            raise EvalError("'sort' requires a list")
        try:
            return sorted(lst)
        except TypeError:
            raise EvalError("Cannot sort this list — items must be comparable")

    def epp_reversed(args):
        lst = args[0] if args else []
        if isinstance(lst, list):
            return list(reversed(lst))
        if isinstance(lst, str):
            return lst[::-1]
        raise EvalError("'reversed' requires a list or string")

    def epp_sum(args):
        lst = args[0] if args else []
        if not isinstance(lst, list):
            raise EvalError("'sum' requires a list of numbers")
        total = 0
        for item in lst:
            if not isinstance(item, (int, float)) or isinstance(item, bool):
                raise EvalError("'sum' requires a list of numbers")
            total += item
        return total

    def epp_slice(args):
        seq = args[0] if args else None
        start = int(args[1]) if len(args) > 1 else 0
        end = int(args[2]) if len(args) > 2 else None
        if seq is None:
            return '' if False else []
        if end is None:
            end = len(seq)
        result = seq[start:end]
        return result

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
                f.write(evaluator.to_display_string(content))
        except IOError as e:
            raise EvalError(f"Cannot write file '{path}': {e}")
        return None

    def epp_append_file(args):
        path = args[0] if args else ''
        content = args[1] if len(args) > 1 else ''
        try:
            with open(path, 'a') as f:
                f.write(evaluator.to_display_string(content))
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

    def epp_seed(args):
        n = args[0] if args else 0
        random.seed(n)
        return None

    def epp_random_int(args):
        low = int(args[0]) if args else 0
        high = int(args[1]) if len(args) > 1 else 100
        if low > high:
            low, high = high, low
        return random.randint(low, high)

    def epp_shuffle(args):
        lst = args[0] if args else None
        if not isinstance(lst, list):
            raise EvalError("'shuffle' requires a list")
        random.shuffle(lst)
        return None

    def epp_time(args):
        return time.time()

    def epp_clock(args):
        """Human-readable current time string."""
        return time.strftime('%Y-%m-%d %H:%M:%S')

    def epp_sleep(args):
        seconds = args[0] if args else 1
        try:
            time.sleep(float(seconds))
        except ValueError:
            raise EvalError(f"'sleep' requires a number")

    def epp_abs(args):
        val = args[0] if args else 0
        return abs(val)

    def epp_round(args):
        val = args[0] if args else 0
        digits = int(args[1]) if len(args) > 1 else 0
        result = round(float(val), digits)
        return int(result) if digits <= 0 else result

    def epp_floor(args):
        return math.floor(float(args[0] if args else 0))

    def epp_ceil(args):
        return math.ceil(float(args[0] if args else 0))

    def epp_pow(args):
        base = args[0] if args else 0
        exp = args[1] if len(args) > 1 else 1
        return base ** exp

    def epp_min(args):
        vals = args[0] if args and len(args) == 1 and isinstance(args[0], list) else args
        if not vals:
            raise EvalError(f"'min' needs at least one value")
        return min(vals)

    def epp_max(args):
        vals = args[0] if args and len(args) == 1 and isinstance(args[0], list) else args
        if not vals:
            raise EvalError(f"'max' needs at least one value")
        return max(vals)

    def epp_sqrt(args):
        val = args[0] if args else 0
        if isinstance(val, (int, float)) and val < 0:
            raise EvalError("Cannot take the square root of a negative number")
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

    def epp_fetch_json(args):
        text = epp_fetch(args)
        return epp_parse_json([text])

    def epp_parse_json(args):
        import json
        text = args[0] if args else ''
        try:
            return json.loads(text)
        except Exception as e:
            raise EvalError(f"Cannot parse JSON: {e}")

    def epp_to_json(args):
        import json
        obj = args[0] if args else None
        try:
            return json.dumps(obj, indent=2)
        except Exception as e:
            raise EvalError(f"Cannot convert to JSON: {e}")

    stdlib = {
        # Output & input
        'say': lambda ev, args: epp_say(args),
        'input': lambda ev, args: epp_input(args),
        # Types & conversion
        'type': lambda ev, args: epp_type(args),
        'len': lambda ev, args: epp_len(args),
        'int': lambda ev, args: epp_int(args),
        'float': lambda ev, args: epp_float(args),
        'str': lambda ev, args: epp_str(args),
        'bool': lambda ev, args: epp_bool(args),
        # Collections
        'range': lambda ev, args: epp_range(args),
        'push': lambda ev, args: epp_push(args),
        'pop': lambda ev, args: epp_pop(args),
        'keys': lambda ev, args: epp_keys(args),
        'values': lambda ev, args: epp_values(args),
        'contains': lambda ev, args: epp_contains(args),
        'index_of': lambda ev, args: epp_index_of(args),
        'sort': lambda ev, args: epp_sort(args),
        'reversed': lambda ev, args: epp_reversed(args),
        'sum': lambda ev, args: epp_sum(args),
        'slice': lambda ev, args: epp_slice(args),
        # Strings
        'split': lambda ev, args: epp_split(args),
        'join': lambda ev, args: epp_join(args),
        'trim': lambda ev, args: epp_trim(args),
        'replace': lambda ev, args: epp_replace(args),
        'upper': lambda ev, args: epp_upper(args),
        'lower': lambda ev, args: epp_lower(args),
        # Files
        'read_file': lambda ev, args: epp_read_file(args),
        'write_file': lambda ev, args: epp_write_file(args),
        'append_file': lambda ev, args: epp_append_file(args),
        'exists': lambda ev, args: epp_exists(args),
        'delete_file': lambda ev, args: epp_delete_file(args),
        # Numbers
        'abs': lambda ev, args: epp_abs(args),
        'round': lambda ev, args: epp_round(args),
        'floor': lambda ev, args: epp_floor(args),
        'ceil': lambda ev, args: epp_ceil(args),
        'pow': lambda ev, args: epp_pow(args),
        'sqrt': lambda ev, args: epp_sqrt(args),
        'min': lambda ev, args: epp_min(args),
        'max': lambda ev, args: epp_max(args),
        # Randomness & time
        'random': lambda ev, args: epp_random(args),
        'seed': lambda ev, args: epp_seed(args),
        'random_int': lambda ev, args: epp_random_int(args),
        'shuffle': lambda ev, args: epp_shuffle(args),
        'time': lambda ev, args: epp_time(args),
        'clock': lambda ev, args: epp_clock(args),
        'sleep': lambda ev, args: epp_sleep(args),
        # Networking & JSON
        'fetch': lambda ev, args: epp_fetch(args),
        'fetch_json': lambda ev, args: epp_fetch_json(args),
        'parse_json': lambda ev, args: epp_parse_json(args),
        'to_json': lambda ev, args: epp_to_json(args),
    }
    for name, func in stdlib.items():
        func._epp_native = True
    return stdlib
