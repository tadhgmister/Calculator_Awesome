from . import environ, parsing

from IPython.core.magic import (Magics, magics_class, line_magic,
                                cell_magic, line_cell_magic)
from IPython.display import display_latex


import traceback, sys
def printf(line):
    if line is None:
        return
    line = line.strip("$")
    if line:
        display_latex("$"+line+"$", raw=True)
def display_error(e):
    print(*traceback.format_exception_only(type(e),e), sep="", file=sys.stderr)
def print_steps(node, debug=False, compact=False):
    first = None
    try:
        it = parsing.step_strings(node)
        first = next(it)
        lines = [first, *it]
    except Exception as e:
        if debug: #and not isinstance(e.__cause__,environ.UserError):
            raise
        else:
            printf(first)
            display_error(e)
            return
    last_line = None
    printed = False
    for line in lines:
        if line == last_line:
            continue
        printf(line)
        printed = True
        last_line = line
    if printed and not compact:
        print()
    
def exec(text, *, debug=False, compact=False):
    module = parsing.parse_expression(text)
    for node in module.body:
        print_steps(node, debug, compact)
    

# The class MUST call this class decorator at creation time
@magics_class
class CalcMagics(Magics):
    
    @line_cell_magic
    def calc(self, line, cell=None):
        "Magic that works both as %lcmagic and as %%lcmagic"
        if cell is None:
            exec(line)
        else:
            debug = ("debug=True" in line)
            compact = ("compact=True" in line)
            exec(cell, debug=debug, compact=compact)
            

def initialize(ipython):
    environ.locals = environ.namespace.maps[0] = ipython.user_global_ns
    ipython.register_magics(CalcMagics)
    environ.set_default_spec("~L")
