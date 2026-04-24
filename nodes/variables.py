import ast, types

from .. import environ, shorthand

from . import Node, register_conv, precedence_reference
from . import constructs, operations

@register_conv
class Variable(ast.Name, Node):
    __slots__ = ()
    def __new__(cls, id, ctx):
        #first check if this was a keyword that needed to be modified
        if id.endswith("_"):
            without_tail = id[:-1]
            if without_tail in shorthand.keywords_allowed_as_identifiers:
                id = without_tail
            
        return super().__new__(cls, id, ctx)
        
    def represent(self, *a,**kw):
        spec = environ.get_spec(*a, **kw)
        name = format_name(self.id, spec)
        if(isinstance(self.ctx, ast.Load)
          and self.id not in environ.locals
          and self.id in environ.globals
          ):
            #do special treatment to loading global variables
            val = environ.globals.get(self.id)
            try:
                return environ._try_special_format(val, spec)
            except LookupError:
                pass
    
        if self.id in environ.namespace:
            value = environ.namespace[self.id]
            try:
                special_method = value.__repr_var__
            except AttributeError:
                pass
            else:
                return special_method(name, spec)
        return name
    
    def substitute(self, *a,**kw):
        if not isinstance(self.ctx, ast.Load):
            return self
        try:
            val = environ.namespace[self.id]
        except KeyError:
            #we are probably getting a NameError soon
            #although this will happen with multiple statements like "x = 5; x+2"
            return self
        rep = repr(val)
        if rep == str(val) and rep.startswith("<") and rep.endswith(">"):
            #things that would be badly represented should stay as names
            #this is probably implemented in wrong place but right now this is to display functions as just the name
            return self
            
        elif self.id in environ.locals: #!!!!!!
            return Value(environ.locals[self.id], substituted=True)
        elif self.id in environ.globals:
            return Value(environ.globals[self.id], id=self.id)
        else:
            return self # probably will end up with name error? might be worth replacing with 'undefined' or something but probably best to just let the actual error happen at evaluation step.

    def evaluate(self, *a, **kw):
        assert isinstance(self.ctx, ast.Load), "can only evaluate name when loading"
        try:
            return environ.namespace[self.id]
        except (NameError, KeyError) as e:
            raise e from environ.UserError

## since program was written Num and NamedConstant were deprecated for Constant

# @register_conv
# class NamedConstant(ast.NameConstant, Node):
#     """supports both python NameConstant like True, False, None
# also used as intermidiate step for substituting values from a module."""
    
#     def __new__(cls, value, id=None):
#         return super().__new__(cls, value)
#     def __init__(self, value, id=None):
#         super().__init__(value)
#         if id is None:
#             id = str(value)
#         self.id = id

#     def represent(self,*a,**kw):
#         spec = environ.get_spec(*a, **kw)
#         val = self.value
#         try:
#             return environ._try_special_format(val, spec)
#         except LookupError:
#             return format_name(self.id, spec)
#     def substitute(self, *a,**kw):
#         return self
#     def evaluate(self, *a,**kw):
#         return self.value

@register_conv
class Value(ast.Constant, Node):
    def __new__(cls, value, kind=None, *, id=None,substituted=False):
        inst = super().__new__(cls, value,kind)
        inst.__always_use_parens = substituted
        inst.__named_id = id
        return inst
    def represent(self, *a,**kw):
        spec = environ.get_spec(*a,**kw)
        if self.__named_id is not None:
            return format_name(self.__named_id, spec)
##        print("representing Value with spec = "+repr(spec))
        rep = environ.format(self.value, spec)
        if self.__always_use_parens:
            rep = environ.add_parens(rep)
        return rep
    
    def substitute(self, *a,**kw):
        return self

    def evaluate(self, *a,**kw):
        return self.value



######################### Attribute lookup #################

@register_conv
class Attribute(ast.Attribute, Node):
    __slots__ = ()
    _eval_on_sub = {"std_dev","nominal_value", "s", "n",
                    "magnitude", "units", "m", "u",
                    "T"}
    def __new__(cls, value, attr, ctx):
        if (isinstance(ctx, ast.Load)
            and isinstance(value, constructs.Array)
            and attr=="T"):
            return value.transpose()
        else:
            return super().__new__(cls, value, attr,ctx)
    def represent(self, *a,**kw):
        val = self.value.represent(*a,**kw)
        if self.value.precedence < self.precedence:
            val = environ.add_parens(val)
        attr = format_name(self.attr, environ.get_base_spec(*a, **kw))
        return ".".join([val,attr])
        
    def substitute(self, *a,**kw):
        if self.attr in self._eval_on_sub:
            return Value(self.evaluate(*a,**kw), substituted=True)
        val = self.value.substitute(*a,**kw)
        #check for module, remove the module lookup if we can.
        if isinstance(val, Value) and isinstance(val.value, types.ModuleType):
            module = val.value #directly using val.value easily causes confusion
            #we are getting the attribute of a module,
            #so we will take out the module part for this step
            try:
                thing = getattr(module, self.attr)
            except AttributeError:
                #we are almost certainly going to get an AttributeError on evaluation
                #so take the path of least resistence
                return self
            else:
                #assuming the attribute evaluates to something show it as just the attribute name
                return Value(thing, id=self.attr, substituted=True)
        elif val is not self.value:
            return Attribute(val, self.attr, self.ctx)
        else:
            return self
                
        
    def evaluate(self, *a,**kw):
        assert isinstance(self.ctx, ast.Load), "can only evaluate attribute when loading"
        val = self.value.evaluate(*a,**kw)
        try:
            return getattr(val, self.attr)
        except AttributeError as e:
            raise e from environ.UserError
    

# ######################### strings #################
# @register_conv
# class Str(ast.Str, Node):
#     __slots__ = ()
#     def represent(self, *a,**kw):
#         return repr(self.s)
#     def substitute(self, *a, **kw):
#         return self
#     def evaluate(self, *a, **kw):
#         return self.s

######################### special name replacements #################

fields = ["P", "L", "H"]
_name_convs = {
            #original    (pretty, latex, mathml) #mathml not supported yet
              'percent': ('%', '\\%', '??'),
              
              'alpha'  : ('α', '\\alpha', '??'),
              'beta'   : ('β', '\\beta', '??'),
              'gamma'  : ('γ', '\\gamma', '??'),
              'delta'  : ('δ', '\\delta', '??'),
              'epsilon': ('ε', '\\epsilon', '??'),
              'zeta'   : ('ζ', '\\zeta', '??'),
              'eta'    : ('η', '\\eta', '??'),
              'theta'  : ('θ', '\\theta', '??'),
              'iota'   : ('ι', '\\iota', '??'),
              'kappa'  : ('κ', '\\kappa', '??'),
              'lambda' : ('λ', '\\lambda', '??'),
              'mu'     : ('μ', '\\mu', '??'),
              'nu'     : ('ν', '\\nu', '??'),
              'xi'     : ('ξ', '\\xi', '??'),
              'omicron': ('ο', 'o', '??'),
              'pi'     : ('π', '\\pi', '??'),
              'rho'    : ('ρ', '\\rho', '??'),
              'sigma'  : ('σ', '\\sigma', '??'),
              'tau'    : ('τ', '\\tau', '??'),
              'upsilon': ('υ', '\\upsilon', '??'),
              'phi'    : ('φ', '\\phi', '??'),
              'chi'    : ('χ', '\\chi', '??'),
              'psi'    : ('ψ', '\\psi', '??'),
              'omega'  : ('ω', '\\omega', '??'),
              
              'Alpha'  : ('Α', 'A', '??'),
              'Beta'   : ('Β', 'B', '??'),
              'Gamma'  : ('Γ', '\\Gamma', '??'),
              'Delta'  : ('Δ', '\\Delta', '??'),
              'Epsilon': ('Ε', 'E', '??'),
              'Zeta'   : ('Ζ', 'Z', '??'),
              'Eta'    : ('Η', 'H', '??'),
              'Theta'  : ('Θ', '\\Theta', '??'),
              'Iota'   : ('Ι', 'I', '??'),
              'Kappa'  : ('Κ', 'K', '??'),
              'Lambda' : ('Λ', '\\Lambda', '??'),
              'Mu'     : ('Μ', 'M', '??'),
              'Nu'     : ('Ν', 'N', '??'),
              'Xi'     : ('Ξ', '\\Xi', '??'),
              'Omicron': ('Ο', 'O', '??'),
              'Pi'     : ('Π', '\\Pi', '??'),
              'Rho'    : ('Ρ', 'P', '??'),
              'Sigma'  : ('Σ', '\\Sigma', '??'),
              'Tau'    : ('Τ', 'T', '??'),
              'Upsilon': ('Υ', '\\Upsilon', '??'),
              'Phi'    : ('Φ', '\\Phi', '??'),
              'Chi'    : ('Χ', 'X', '??'),
              'Psi'    : ('Ψ', '\\Psi', '??'),
              'Omega'  : ('Ω', '\\Omega', '??'),
              }


name_convs = {n:{} for n in fields}

for n, subs in _name_convs.items():
    for let, replace in zip(fields, subs):
        name_convs[let][n] = replace


def replace_name_latex(name):
    convs = name_convs["L"]
    if name.count("_") == 1:
        a,b = name.split("_")
        if len(a)==1 or a in convs:
            result =  convs.get(a,a)
            if b in convs:
                result += "_"+convs[b]
            elif b:
                result += "_{%s}"%b
            return result
    return "\\_".join(convs.get(part,part) for part in name.split("_"))

def replace_name_pretty(name):
    convs = name_convs["P"]
    return "_".join(convs.get(part,part) for part in name.split("_"))


formatters = {"L":replace_name_latex,
              "P":replace_name_pretty}

def sub_special_name(name, spec):
    f = formatters.get(environ.base_spec(spec))
    if f:
        return f(name)
    else:
        raise NotImplementedError("no special name to format")
def format_name(name, spec):
    try:
        return sub_special_name(name, spec)
    except NotImplementedError:
        return name
