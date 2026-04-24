from . import parsing, environ

environ.set_default_spec("P")

##import math
##test_names = ["pi","sin","cos","factorial"]
##environ.globals.update({n:getattr(math,n) for n in test_names})
##
##environ.globals["abs"] = abs

import traceback, sys

def display_error(e):
    print(*traceback.format_exception_only(type(e),e), sep="", file=sys.stderr)

def print_steps(node, last_line=None):
    printed = False
    steps = parsing.step_eval(node)
    try:
        while True:
            a = next(steps)
            line = a.represent()
            if line != last_line:
                printed = True
                print(line)
                last_line = line
    except StopIteration as e:
        if e.value is None:
            return
        line = environ.format(e.value)
        if line != last_line or not printed:
            print(line)
    

while True:
    text = input(">>>")
    if not text:
        break
    try:
        node = parsing.parse_expression(text)
    except SyntaxError as e:
        display_error(e)
        continue
    try:
        print_steps(node, text)
    except (Exception, SyntaxError) as e:
        if isinstance(e.__cause__, environ.UserError):
            display_error(e)
        else:
            traceback.print_exc()
