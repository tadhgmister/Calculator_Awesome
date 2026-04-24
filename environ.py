import ast
import builtins
try:
    import numpy
except ImportError:
    numpy = None
try:
    import sympy
except ImportError:
    sympy = None
    _sympy_formatters = {}
else:
    _sympy_formatters = {"": sympy.printing.srepr,
                         "L":sympy.printing.latex,
                         "P":sympy.printing.pretty,
                         "H":sympy.printing.mathml}

from collections import ChainMap as _ChainMap
from . import shorthand

try:
    from uncertainties.core import AffineScalarFunc as uVar
except ImportError:
    uVar = None
try:
    import pint
except ImportError:
    pint = None

_namespace_note = """
namespace is a chainmap that contains (locals, globals) and should not be modified further
locals is a basic dictionary to hold well defined variables (ones the user has specified by name)
globals is a chain map of all module that were imported as "from x import *" (so the user did not specify their name)

originally globals.maps[0] was where imported names went to (so "import math" would put the math module in globals)
however this became an issue when names were alreaady defined locally, for example this:

sin = 5
from math import sin

would put "sin=5" in the locals and "sin = <function>" in globals so the function would be inaccessable

Now globally imported names are put in the local namespace so the above example will overide 5 with the function but
the following example still has issues:

sin = 5
from math import *

this will put the math module in globals.maps while "sin=5" is still in locals.
since there are modules that dynamically generate members (such as symbolic) I'm not
sure how to implement the namespace so the most recent import is available first while still
maintaining the right to dynamically create module members and allow other parts to check for "global variables"
"""

locals = {}
globals = _ChainMap({"None":None, "True":True, "False":False, "help":help})
namespace = _ChainMap(locals, globals)

default_spec = ""
_spec_update_callbacks = []
def set_default_spec(new_spec):
    global default_spec
    default_spec = new_spec
    for func in _spec_update_callbacks:
        func(new_spec)

_specs = {"":"text",
          "L":"latex",
          "H":"html",
          "P":"pretty"}


                     
def base_spec(spec):
    """returns one of the implemented specifiers
(currently only removes ~ from the specifier)"""
    new_spec = spec.replace("~","")
    if new_spec not in _specs:
        raise ValueError("cannot recognize spec %r"%spec)
    return new_spec
def get_spec(*a, **kw):
    "extracts spec keyword or returns the default spec"
    spec = kw.get("spec")
        #spec in default spec means it's a subset of the default spec, like spec='L' and default_spec='~L'
    if spec is None or spec in default_spec:
        spec = default_spec
    return spec
def get_base_spec(*a,**kw):
    "shorthand for base_spec(get_spec(*a,**kw))"
    return base_spec(get_spec(*a,**kw))



class UserError(Exception):
    """use "raise err from environ.UserError" to indicate that an error is intended for the user"""



#### formatting ####

def add_parens(string:str, spec=None, force = False):
    #at some point will update to check that it doesn't already have parens, where force will force it.
    if spec is None:spec = default_spec
    if "L" in spec:
        return "\\left( %s \\right)"%string
    else:
        return "(%s)"%string


def format(obj, spec=None):
    if spec is None:
        spec = default_spec
    base_s = base_spec(spec)
    if numpy and isinstance(obj, numpy.ndarray) and "L" in spec:
        return latex_repr_array(obj)
    elif pint and isinstance(obj, pint.Quantity):
        mag = format(obj.magnitude, spec)
        units = format(obj.units, spec)
        sep = ""
        if "L" in spec:
            sep = "\\,"
            if "%" in units:
                units = units.replace("%", "\\%")
        if uVar and isinstance(obj.magnitude, uVar):
            mag = add_parens(mag)
        
        return mag+sep+units
    elif sympy and isinstance(obj, sympy.Basic):
        return _sympy_formatters[base_s](obj)
    try:
        return _try_special_format(obj, spec)
    except LookupError:
        pass
    #the following is in a loop due to old method of processing data
    #will probably factor out if I decide to not use multiple variations of the spec.
    for fallback_spec in (spec,base_spec(spec)): 
        try:
            return builtins.format(obj, fallback_spec)
        except ValueError:
            pass
        except TypeError:
            break #objects that do not support format at all should just skip to str(obj)
    
    s = str(obj)
    if "L" in spec:
        s = latex_escape(s)
    return s

def _try_special_format(self, spec=None):
    if spec is None:spec = default_spec
    spec_name = _specs.get(spec)
    if spec_name:
        method_name = "_repr_{}_".format(spec_name)
        direct_method = getattr(type(self), method_name, None)
        if direct_method:
            result = direct_method(self)
            if spec_name=="latex" and result.startswith("$") and result.endswith("$"):
                result = result.strip("$")
            return result

    raise LookupError("no applicable special formatting found")


def _latex_row(row, spec):
    "helper for latex_repr_array"
    return " & ".join([format(i,"L") for i in row])
def latex_repr_array(array, spec="L"):
    if len(array.shape) == 1:
        s = _latex_row(array, spec)
    elif len(array.shape) == 2:
        s= " \\\\\n".join([_latex_row(row, spec) for row in array])
    else:
        raise TypeError("cannot represent array with more then 2 dimensions")
    return "\\left( \\begin{matrix}"+ s +"\\end{matrix} \\right)"

def latex_escape(s):
    escape_chars = " _$%"
    for c in escape_chars:
        s = s.replace(c, "\\"+c)
    return s
