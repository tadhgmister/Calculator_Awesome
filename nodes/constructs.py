import ast
import types
import operator


from . import (register_conv, Node, node_conversions)
from . import variables
from .operations import Operation, BinOp
from .. import environ, packages


####################### Module, Expr, Assign #################

@register_conv
class Module(ast.Module, Node):
    __slots__ = ()
    
    def represent(self, *a,**kw):
        return "\n".join([b.represent(*a,**kw) for b in self.body])

    def substitute(self, *a,**kw):
        new_body = [b.substitute(*a,**kw) for b in self.body]
        if all((old is new) for old, new in zip(self.body, new_body)):
            return self
        else:
            return Module(new_body)

    def evaluate(self, *a,**kw):
        """evaluates all nodes in the body, returns None"""
        for b in self.body:
            b.evaluate(*a,**kw)

        
@register_conv
class Expr(ast.Expr, Node):
    __slots__ = ()
    def represent(self, *a,**kw):
        return self.value.represent(*a,**kw)
    def substitute(self, *a,**kw):
        return self.value.substitute(*a,**kw)
    def evaluate(self, *a,**kw):
        return self.value.evaluate(*a,**kw)

#*# At some point I will confirm that the below statement works and probably use it instead

### ast.Expr basically represents "expression that the value is thrown away"
### this detail isn't really necessary so the value should just be directly returned
#node_conversions[ast.Expr] = lambda x:x
    

@register_conv
class Assign(ast.Assign, Node):
    __slots__ = ()
    def __format__(self, spec):
        return self.represent(spec=spec)
    def __str__(self):
##        import traceback
##        traceback.print_stack()
##        print("USED __str__ ON ASSIGN")
        return self.represent()
    def represent(self, *a,**kw):
        targets = (target.represent(*a,**kw) for target in self.targets)
        value = self.value.represent(*a,**kw)
        if "=" in value:
            value = environ.add_parens(value, environ.get_spec(*a,**kw))
        if environ.get_base_spec(*a, **kw) == "L":
            sep = " = " #adding the & seems to align multiple equations nicely 
        else:
            sep = " = "
        return sep.join([*targets, value])
        
    def substitute(self, *a,**kw):
        subbed_targets = [t.substitute(*a,**kw) for t in self.targets]
        val = self.value.substitute(*a,**kw)
        if val is self.value and all((new is old) for new, old in zip(subbed_targets, self.targets)):
            return self
        else:
            return Assign(subbed_targets, val)
        
    def evaluate(self, *a,**kw):
        val = self.value.evaluate(*a,**kw)
        for target in self.targets:
            self.do_assignment(target, val)
        return Assign(self.targets, variables.Value(val))
    @classmethod
    def do_assignment(cls, target, value):
        if isinstance(target, ast.Name):
            environ.namespace[target.id] = value
        elif isinstance(target, ast.List):
            value = list(value)
            if len(value) != len(target.elts):
                raise ValueError("not the right number of elements to unpack\n"\
                                 "expected {} but got {}".format(len(target.elts), len(value)))
            for t,v in zip(target.elts, value):
                cls.do_assignment(t, v)
        elif isinstance(target, ast.Subscript):
            container = target.value.evaluate()
            index = target.slice.evaluate()
            container[index] = value

        else:
            raise NotImplementedError("assignment to %r is not supported"%type(target)) from environ.UserError


        

#
######################### Import #################
####
#### cannot use vars when module overrides __getattr__
##def _map_proxy(package):
##    "takes a package and returns a dictionary-like view on it's members"
##    return vars(package)

class _map_proxy:
    def __init__(self, package):
        "takes a package and returns a dictionary-like view on it's members"
        self.package = package
    def keys(self):
        return dir(self.package)
    def __getitem__(self, key):
        try:
            return getattr(self.package, key)
        except AttributeError:
            raise KeyError(key) from None
    def __contains__(self, key):
        return hasattr(self.package, key)
    def __setitem__(self, key, value):
        return setattr(self.package, key, value)
    
def load_names_from_package(node, package):
    """common tool for Import and ImportFrom, generates (name, value) for each alias in node.names"""
    for alias in node.names:
        if alias.name == "*":
            #remove it before adding again if already imported
            for i,p in enumerate(environ.globals.maps):
                if p.package is package:
                    del environ.globals.maps[i]
                    break
            #globals.maps[0] is reserved for specific imports
            environ.globals.maps.insert(1, _map_proxy(package))
        else:
            yield alias.load_from(package)
        

@register_conv
class Import(ast.Import, Node):
    __slots__ = ()
    def represent(self, *a,**kw):
        names = ", ".join([al.represent(*a, **kw) for al in self.names])
        return "import "+names
    def substitute(self, *a, **kw):
        return self
    def evaluate(self, *a, **kw):
        environ.globals.update(load_names_from_package(self, packages))
        return None
    
@register_conv
class ImportFrom(ast.ImportFrom, Node):
    def represent(self, *a,**kw):
        names = ", ".join([al.represent(*a, **kw) for al in self.names])
        return "from {self.module} import {names}".format(names=names, self=self)
    def substitute(self, *a, **kw):
        return self
    def evaluate(self, *a, **kw):
        module = getattr(packages, self.module)
        environ.globals.update(load_names_from_package(self, module))
        return None


@register_conv
class alias(ast.alias, Node):
    """currently this only exists to disallow 'import x as y' since importing is handled differently
otherwise I could just do `conversions[ast.alias] = ast.alias` to make it work"""
    __slots__ = ()
    def represent(self, *a,**kw):
        if self.asname is None:
            return self.name
        else:
            return self.name+" as "+self.asname

    def substitute(self,*a,**kw):
        return self
    def evaluate(self, *a,**kw):
        raise TypeError("cannot evaluate aliasses")
    def load_from(self, package):
        n = self.asname or self.name
        try:
            return n, getattr(package, self.name)
        except AttributeError:
            raise ImportError("cannot import name {self.name!r}".format(self=self)) from environ.UserError
        
        

######################### Comparisons #################

import itertools
try:
    import sympy
    from sympy.logic.boolalg import BooleanFalse, BooleanTrue
    sympy_bool_types = (BooleanFalse, BooleanTrue)
except ImportError:
    sympy = None
    sympy_bool_types = ()

try:
    import numpy
except ImportError:
    numpy = None
    

def equal(a,b):
    if sympy and (isinstance(a, sympy.Basic) or isinstance(b, sympy.Basic)):
        if sympy.simplify(a-b)==0:
            return True
        else:
            print("returned Eq")
            return sympy.Eq(a, b)
    elif isinstance(a, float) and isinstance(b, float):
        return str(a) == str(b)
    else:
        return a == b
    
def not_equal(a,b):
    if sympy and (isinstance(a, sympy.Basic) or isinstance(b, sympy.Basic)):
        if sympy.simplify(a-b)==0:
            return False
        else:
            return sympy.Not(sympy.Eq(a,b))
    else:
        return a != b

def is_(a,b):
    if sympy and (isinstance(a, sympy.Basic) or isinstance(b, sympy.Basic)):
        return sympy.simplify(a-b)==0
    result = (a == b)
    if numpy and isinstance(result, numpy.ndarray):
        return result.all() #only the same if all are the same
    elif result in (True, False):
        return result
    else:
        raise TypeError("== returned non-recognized type: %r"%type(result))
    
def is_not(a,b):
    if sympy and (isinstance(a, sympy.Basic) or isinstance(b, sympy.Basic)):
        return sympy.simplify(a-b)!=0
    result = (a != b)
    if numpy and isinstance(result, numpy.ndarray):
        return result.any() #if any are different then they are not identical
    elif result in (True, False):
        return result
    else:
        raise TypeError("!= returned non-recognized type: %r"%type(result))
    

@register_conv
class Compare(ast.Compare, Operation):
    __slots__ = ()
    _op_symbols = {ast.Lt:    "<",
                   ast.LtE:   "<=",
                   ast.Gt:    ">",
                   ast.GtE:   ">=",
                   ast.Eq:    "==",
                   ast.NotEq: "!=",
                   ast.Is:    " is ",
                   ast.IsNot: " is not "}
    _op_funcs = {  ast.Lt:    operator.lt,
                   ast.LtE:   operator.le,
                   ast.Gt:    operator.gt,
                   ast.GtE:   operator.ge,
                   ast.Eq:    equal, 
                   ast.NotEq: not_equal,
                   ast.Is:    is_,
                   ast.IsNot: is_not} 

    
    def iter_args(self):
        yield self.left
        yield from self.comparators
    def pairs(self):
        return zip(self.ops, self.comparators)
    
    def represent(self, *a, **kw):
        s = self.left.represent(*a, **kw)
        for op, arg in self.pairs():
            arg_rep = arg.represent(*a, **kw)
            if arg.precedence < self.precedence:
                arg_rep = environ.add_parens(arg_rep)
            s += "{op}{arg}".format(op=self._op_symbols[type(op)],
                                      arg=arg_rep)
        return s
    def substitute(self, *a, **kw):
        args = [arg.substitute(*a, **kw) for arg in self.iter_args()]
        if all((new is old) for new,old in zip(args, self.iter_args())):
            return self
        else:
            left, *comps = args
            return Compare(left, self.ops, comps)

    def as_singles(self):
        l = self.left
        for op, r in self.pairs():
            yield Compare(l, [op], [r])
            l = r
    
    def evaluate(self, *a, **kw):
        if len(self.ops)>1:
            return BoolOp(ast.And(), list(self.as_singles())).evaluate(*a, **kw)
        else:
            left = self.left.evaluate(*a, **kw)
            right = self.comparators[0].evaluate(*a, **kw)
            func = self._op_funcs[type(self.ops[0])]
            
            val = func(left, right)
            if isinstance(val, sympy_bool_types):
                val = bool(val)
            return val
            
######################### Logical #################



logic_symbols = {
                 "" :{ast.And:" and ",   ast.Or:" or "},
                 "L":{ast.And:"\\wedge ", ast.Or:"\\vee "},
                 "P":{ast.And:"⋀",       ast.Or:"⋁"},
                }

@register_conv
class BoolOp(ast.BoolOp, Operation):
    __slots__ = ()
    
    def represent(self, *a,**kw):
        spec = environ.get_base_spec(*a, **kw)
        if spec not in logic_symbols:
            spec = ""
        symbol = logic_symbols[spec][type(self.op)]
        args = [self.format_arg(arg, True, *a, **kw) for arg in self.values]
        return symbol.join(args)

    def substitute(self, *a,**kw):
        args = [arg.substitute(*a,**kw) for arg in self.values]
        if all(new is old for new,old in zip(args, self.values)):
            return self
        else:
            return BoolOp(self.op, args)

    def evaluate(self, *a,**kw):
        gen = (arg.evaluate(*a, **kw) for arg in self.values)
        if isinstance(self.op, ast.And):
            try:
                from sympy import And as func
                from sympy.logic.boolalg import BooleanFalse as break_type
            except ImportError:
                def func(a, b):
                    return bool(a and b)
                break_type = ()
            break_val = False
        elif isinstance(self.op, ast.Or):
            try:
                from sympy import Or as func
                from sympy.logic.boolalg import BooleanTrue as break_type
            except ImportError:
                def func(a, b):
                    return bool(a or b)
                break_type = ()
            break_val = True
        else:
            raise ValueError("not recognized bool op "+repr(self.op))
        val = next(gen)
        for arg in gen:
            val = func(val,arg)
            if isinstance(val, break_type) or val is break_val:
                return break_val
        if isinstance(val, sympy_bool_types):
            val = bool(val)
        return val
    
try:
    import sympy
except ImportError:
    pass
else:
    class RShift(BinOp):
        """used or logical 'implies'"""
        from sympy.logic.boolalg import Implies as func
        def get_symbol(self, spec):
            if spec == "L":
                return "\\rightarrow"
            elif spec == "P":
                return "⇒"
            else:
                return "->"

        def evaluate(self, *a, **kw):
            result = super().evaluate(*a, **kw)
            #ensure that sympy booleans are returned as proper booleans
            if isinstance(result, sympy_bool_types):
                result = bool(result)
            return result


            


######################### Vectors and Arrays #################

@register_conv
class Vector(ast.List, Node):
    """use lists for vectors"""
    def __new__(cls, elts, ctx):
        if isinstance(ctx, ast.Load):
            l = len(elts)
            if l == 2:
                elts.append(variables.Value(0))
            elif l!=3:
                raise TypeError("can only have vectors of length 3 (or 2)")
        return super().__new__(cls, elts, ctx)
    
    def represent(self, *a, **kw):
        elements = [i.represent(*a, **kw) for i in self.elts]
        spec = environ.get_base_spec(*a, **kw)
        if spec == "L":
            head = "\\begin{bmatrix}"
            sep = "\\\\"
            tail = "\\end{bmatrix}"
        else:
            head, tail = "[]"
            sep = ", "
        return head + sep.join(elements) + tail

    def substitute(self, *a, **kw):
        items = [i.substitute(*a, **kw) for i in self.elts]
        if all(new is old for new,old in zip(items, self.elts)):
            return self
        else:
            return Vector(items, self.ctx)

    def evaluate(self, *a, **kw):
        items = (i.evaluate(*a, **kw) for i in self.elts)
        return packages.vectors.Vector(*items)

try:
    import numpy
except ImportError:
    class Array():
        "placeholder for things that check for the existance"
else:
    @register_conv
    class Array(ast.Tuple, Node):
        """use tuples as numpy arrays"""
        def is_nested(self):
            """returns True if all elements are Arrays"""
            return all(isinstance(i, Array) for i in self.elts)
        def represent(self, *a, **kw):
            spec=  environ.get_base_spec(*a, **kw)
            nested = self.is_nested()
            if spec == "L":
                if kw.get("inner_matrix"):
                    head = ""
                    tail = ""
                    sep = "&"
                else:
                    head = "\\left(\\begin{matrix}"
                    tail = "\\end{matrix}\\right)"
                    if nested:
                        sep = "\\\\\n" #seperation for outer is newlines
                    else:
                        sep = "&"
            else:
                head = "("
                tail = ")"
                sep = ", "
            if nested:
                kw["inner_matrix"] = True #sub arrays will check for this
            items = [item.represent(*a, **kw) for item in self.elts]
            return head+ sep.join(items) + tail

        def substitute(self, *a, **kw):
            items = [item.substitute(*a, **kw) for item in self.elts]
            if all(new is old for new,old in zip(items, self.elts)):
                return self
            else:
                return Array(items, self.ctx)

        def evaluate(self, *a, **kw):
            self_is_inner = kw.get("inner_matrix", False)
            kw["inner_matrix"] = True
            items = [item.evaluate(*a, **kw) for item in self.elts]
            if not self_is_inner and not self.is_nested():
                items = [items]
            return numpy.array(items)

        def transpose(self):
            "called by a shortcut in variables.Attribute, takes the transpose"
            if not isinstance(self.ctx, ast.Load):
                raise TypeError("can only take transpose when loading")
            if not self.is_nested():
                new_elts = [Array([item], ast.Load()) for item in self.elts]
                return Array(new_elts, self.ctx)
            else:
    ##            return variables.Attribute(self, "T", ast.Load())
                T = [list(items) for items in zip(*(e.elts for e in self.elts))]
                new_elts = [Array(items, ast.Load()) for items in T]
                return Array(new_elts, self.ctx)



######################### indexing #################

@register_conv
class Subscript(ast.Subscript, Operation):
    def represent(self, *a, **kw):
        val = self.format_arg(self.value, False, *a, **kw)
        slice = self.slice.represent(*a, **kw)
        return "{}[{}]".format(val, slice)

    def substitute(self, *a, **kw):
        from warnings import warn
        warn("substitute is skipped on subscripts")
        return self #I don't care right now

    def evaluate(self, *a, **kw):
        if not isinstance(self.ctx, ast.Load):
            raise ValueError("cannot evaluate Subscript unless it is loading")
        val = self.value.evaluate(*a, **kw)
        slice = self.slice.evaluate(*a, **kw)
        return val[slice]

node_conversions[ast.Index] = lambda x:x #I don't get the point of the Index node
