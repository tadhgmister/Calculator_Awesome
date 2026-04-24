import types

import math as builtin_math

specific_math_modules = {}

from . import sam_math

specific_math_modules[sam_math.SamInt] = sam_math

try:
    from uncertainties import umath
    from uncertainties.core import AffineScalarFunc as uVar
except ImportError:
    pass
else:
    specific_math_modules[uVar] = umath

try:
    import numpy
except ImportError:
    pass
else:
    specific_math_modules[numpy.ndarray] = numpy
    
try:
    import sympy
except ImportError:
    pass
else:
    specific_math_modules[sympy.Basic] = sympy

try:
    import cmath
    from builtins import complex
except ImportError:
    pass
else:
    specific_math_modules[complex] = cmath



class _Latex_repr(str):
    def __new__(cls, s, arg_defaults={}):
        s = s.replace("(", "\\left(").replace(")","\\right)")
        return super().__new__(cls, s)
    def __init__(self, s, arg_defaults={}):
        self.arg_defaults = arg_defaults
    @classmethod
    def from_name(cls, s):
        return cls("\\{}({{0}})".format(s))
    def format(self, *args, **kw):
        new_args = {i:v for i,v in self.arg_defaults.items() if isinstance(i, int)}
        new_args.update(enumerate(args))
        args = [new_args[i] for i in sorted(new_args.keys())]
        kw = {**self.arg_defaults, **kw}
        return super().format(*args, **kw)
        
latex_reprs = {n:_Latex_repr.from_name(n) for n in ("sin","cos","tan")}
latex_reprs["log"] = _Latex_repr("log_{1}({0})", {1:"e"})
latex_reprs["sqrt"] = "\\sqrt{{{0}}}"


def wrap_function(func_name, default=None):
    """creates a wrapper function for type-aware processing"""
    if default is None:
        default = getattr(builtin_math, func_name) #if there is no default then this raises the AttributeError
    if not callable(default):
        return default #this isn't a function, just return the value
    def wrapper(*args, **kw):
        if not args:
            return default(*args, **kw) #there are no arguments? This will probably raise a TypeError
        arg = args[0]
        for needed_type, module in specific_math_modules.items():
            if isinstance(arg, needed_type):
                try:
                    use_func = getattr(module, func_name)
                except AttributeError:
                    break #maybe could be continue?
                else:
                    return use_func(*args, **kw)
        else:
            return default(*args,**kw)
    wrapper.__name__ = func_name
    if func_name in latex_reprs:
        wrapper.__repr_func__ = latex_reprs[func_name].format
    return wrapper


class math_module(types.ModuleType):
    def __getattr__(self, name):
        if name == "tau":
            raise AttributeError("tau is specifically blacklisted on the math module")
        new_attr = wrap_function(name)
        setattr(self, name, new_attr)
        return new_attr

math = math_module("math")
def abs_wrapper(x):
    return abs(x)
abs_wrapper.__repr_func__ = "\\left|{0}\\right|".format
math.abs = abs_wrapper #note we are adding this to the math module, not monkeypatching the builtin one.
#because __abs__ can be overriden by the argument there is no need to do any wrapping for this one.

_fallback_sqrt = builtin_math.sqrt
def alt_sqrt(x):
    """tries to use the builtin sqrt, if it fails instead returns x**0.5"""
    try:
        return _fallback_sqrt(x)
    except Exception:
        return x**0.5
math.sqrt = wrap_function("sqrt",alt_sqrt) 
math.max = wrap_function("max", max)
math.min = wrap_function("min", min)
