# e++ Language Specification

## Overview

e++ (pronounced "e plus plus") is a beginner-friendly programming language designed to be the easiest language to learn in the world. It features English-like syntax, indentation-based structure, and modern programming constructs.

**Design Goals:**
- Readable like English prose
- Familiar constructs from mainstream languages
- Minimal boilerplate, maximum clarity
- Friendly error messages for beginners

## Basics

### Hello World
```epp
say "Hello, World!"
```

### Comments
```epp
# This is a single-line comment
```

### Variables
Variables are dynamically typed and mutable.
```epp
name = "Alice"
age = 25
pi = 3.14
is_active = true
empty = null
```

### Data Types

| Type | Example | Description |
|------|---------|-------------|
| `int` | `42`, `-7` | Whole numbers |
| `float` | `3.14`, `-0.5` | Decimal numbers |
| `string` | `"Hello"` | Text enclosed in quotes |
| `bool` | `true`, `false` | Logical values |
| `list` | `[1, 2, 3]` | Ordered collection |
| `dict` | `{"name": "Bob", "age": 30}` | Key-value pairs |
| `null` | `null` | Empty or no value |

### Printing Output
```epp
say "Hello!"
say "Value: " + 42
say "Sum: " + (5 + 3)
```

### Getting Input
```epp
name = input("Enter your name: ")
say "Hello, " + name
```

## Operators

### Arithmetic
```epp
a = 10 + 5    # addition
b = 10 - 3    # subtraction
c = 4 * 2     # multiplication
d = 15 / 3    # division
e = 17 % 5    # modulo (remainder)
```

### Comparison (English-like)
```epp
if x is greater than 10:
    say "big"

if name is equal to "Alice":
    say "Hi Alice!"

if age is less than 18:
    say "minor"

if score is greater than or equal to 60:
    say "passed"
```

### Boolean (Words only)
```epp
if x is greater than 10 and x is not equal to 15:
    say "valid"

if is_sunny or is_warm:
    say "nice day"

if not is_raining:
    say "go outside"
```

### Truthy/Falsy
Python-like rules apply:
- `false`, `0`, `""`, `[]`, `{}`, `null` are **falsy**
- Everything else is **truthy**

```epp
if my_list:         # true if list is not empty
    say "has items"
```

## Control Flow

### If / Elif / Else
```epp
if temperature is greater than 30:
    say "hot"
elif temperature is greater than 20:
    say "comfortable"
elif temperature is greater than 10:
    say "cool"
else:
    say "cold"
```

### For Loop
```epp
# Loop through a range
for i in range(5):
    say i

# Loop through a list
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    say fruit
```

### While Loop
```epp
count = 0
while count is less than 5:
    say count
    count = count + 1
```

### Try / Catch
```epp
try:
    result = 10 / 0
catch error:
    say "Error occurred: " + error
```

## Functions

### Defining Functions
```epp
func greet(name):
    say "Hello, " + name

func add(a, b):
    return a + b

func square(x):
    return x * x
```

### Calling Functions
```epp
greet("World")
result = add(5, 3)
area = square(4)
```

### Built-in Functions

**Output/Input:**
- `say(value)` — Print to output
- `input(prompt)` — Get user input

**Type Conversion:**
- `type(x)` — Return type name as string
- `str(x)` — Convert to string
- `int(x)` — Convert to integer
- `float(x)` — Convert to float
- `bool(x)` — Convert to boolean

**Collections:**
- `len(x)` — Return length of list or string
- `range(n)` — Return list from 0 to n-1
- `push(list, item)` — Add item to list
- `pop(list)` — Remove and return last item
- `keys(dict)` — Return list of dict keys
- `values(dict)` — Return list of dict values

**Strings:**
- `split(str, delimiter)` — Split string into list
- `join(list, delimiter)` — Join list into string
- `trim(str)` — Remove leading/trailing whitespace
- `replace(str, old, new)` — Replace substring

**Files:**
- `read_file(path)` — Read entire file as string
- `write_file(path, content)` — Write content to file (overwrites)
- `append_file(path, content)` — Append content to file
- `exists(path)` — Return true if file exists
- `delete_file(path)` — Delete a file

**System:**
- `random()` — Return random float 0-1
- `time()` — Return current timestamp
- `sleep(seconds)` — Pause execution

## Classes

### Defining Classes
```epp
class Animal:
    func init(name):
        self.name = name

    func speak():
        say self.name + " makes a sound"
```

### Using Classes
```epp
dog = Animal("Rex")
dog.speak()
say dog.name
```

### Class Methods
```epp
class Counter:
    func init():
        self.count = 0

    func increment():
        self.count = self.count + 1

    func get_count():
        return self.count

counter = Counter()
counter.increment()
counter.increment()
say counter.get_count()  # prints 2
```

## Import

### Importing Files
```epp
import "utils.epp"
```
Search order: current folder, then `lib/` folder.

### Example utils.epp
```epp
func add(a, b):
    return a + b

func multiply(a, b):
    return a * b
```

## Standard Library — Full Reference

### Output Functions
| Function | Description | Example |
|----------|-------------|---------|
| `say(value)` | Print value to output | `say "Hello"` |

### Input Functions
| Function | Description | Example |
|----------|-------------|---------|
| `input(prompt)` | Get user input | `name = input("Name: ")` |

### Type Functions
| Function | Description | Example |
|----------|-------------|---------|
| `type(x)` | Return type name | `type(42) → "int"` |
| `str(x)` | Convert to string | `str(3.14) → "3.14"` |
| `int(x)` | Convert to int | `int("42") → 42` |
| `float(x)` | Convert to float | `float("3.14") → 3.14` |
| `bool(x)` | Convert to bool | `bool("") → false` |

### Collection Functions
| Function | Description | Example |
|----------|-------------|---------|
| `len(x)` | Get length | `len([1,2,3]) → 3` |
| `range(n)` | Create range | `range(5) → [0,1,2,3,4]` |
| `push(list, item)` | Add to list | `push(my_list, 4)` |
| `pop(list)` | Remove last | `pop(my_list)` |
| `keys(dict)` | Dict keys | `keys({"a":1}) → ["a"]` |
| `values(dict)` | Dict values | `values({"a":1}) → [1]` |

### String Functions
| Function | Description | Example |
|----------|-------------|---------|
| `split(str, delim)` | Split string | `split("a,b", ",") → ["a","b"]` |
| `join(list, delim)` | Join list | `join(["a","b"], "-") → "a-b"` |
| `trim(str)` | Remove spaces | `trim("  hi  ") → "hi"` |
| `replace(str, old, new)` | Replace text | `replace("hi hi", "hi", "yo") → "yo yo"` |

### File Functions
| Function | Description | Example |
|----------|-------------|---------|
| `read_file(path)` | Read file | `content = read_file("test.txt")` |
| `write_file(path, content)` | Write file | `write_file("out.txt", "hi")` |
| `append_file(path, content)` | Append | `append_file("log.txt", "log")` |
| `exists(path)` | Check existence | `exists("data.txt")` |
| `delete_file(path)` | Delete file | `delete_file("temp.txt")` |

### System Functions
| Function | Description | Example |
|----------|-------------|---------|
| `random()` | Random float | `random()` |
| `time()` | Timestamp | `time()` |
| `sleep(sec)` | Pause | `sleep(1)` |

## Error Messages

e++ provides friendly, beginner-friendly error messages:

**Example errors:**
```
Error at line 5: I expected 'if' here — did you mean 'if'?
Error at line 10: 'name' is not defined. Did you forget to assign it?
Error at line 15: Cannot divide by zero
Error at line 20: 'add' is not a function — it has no return value
```

## Reserved Words

```
func, class, if, elif, else, for, while, return, say,
in, and, or, not, null, true, false, self,
import, try, catch, is, is not,
is greater than, is less than, is equal to,
is greater than or equal to, is less than or equal to
```

## Grammar Summary

```
program       → statement*
statement     → func_def | class_def | if_stmt | for_stmt
              | while_stmt | try_catch | return_stmt | import_stmt | expr_stmt
func_def      → "func" IDENT "(" params? ")" ":" block
class_def     → "class" IDENT ":" block
if_stmt       → "if" expr ":" block ("elif" expr ":" block)* ("else" ":" block)?
for_stmt      → "for" IDENT "in" expr ":" block
while_stmt    → "while" expr ":" block
try_catch     → "try" ":" block "catch" IDENT ":" block
return_stmt   → "return" expr?
import_stmt   → "import" STRING
block         → INDENT statement* DEDENT
expr          → assignment | comparison | term | factor | unary | primary
```

## File Extension

All e++ source files use the extension: `.epp`