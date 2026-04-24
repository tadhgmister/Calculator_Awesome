import ast
import operator

from . import (Node, register_conv, precedence_reference)
from . import variables
from .. import environ


#TO DO: Check how keyword arguments work on the Call operation

class Operation(Node):
    """specifies an operation, contains helper functions to handle precedence"""
    __slots__ = ()                                  #  ^
    #the docstring is a bit of a lie, there is only one helper function
    def format_arg(self, arg, eq_prec, *a,**kw):
        rep = arg.represent(*a,**kw)
        if eq_prec:
            comp = arg.precedence <= self.precedence
        else:
            comp= arg.precedence < self.precedence
        if comp:
            rep = environ.add_parens(rep)
        return rep


###########  BINARY OPERATORS  #########
#.symbol is the plain text symbol to express the operation
#.func is the function from operator that evaluates the operation
#.order is operation with equal precedence from above list

@register_conv
class BinOp(ast.BinOp, Operation):
    __slots__ = ()
    @property
    def precedence(self):
        return precedence_reference[type(self.op)]
    def get_symbol(self, spec):
        return self.symbol
    
    def _format_operands(self, *a,**kw):
        "use .format_arg() on both .left and .right operands."
        return self.format_arg(self.left,False, *a,**kw), self.format_arg(self.right,True, *a,**kw)
    
    def __new__(cls, left, op, right):
        """when instantiated from BinOp class it will use appropriate subclass for specified op"""
        if cls is not BinOp:
            return super().__new__(cls, left, op, right)
        op_name = op.__class__.__name__
        for cls in BinOp.__subclasses__():
            if cls.__name__ == op_name:
                return cls.__new__(cls, left, op, right)
        raise NotImplementedError("there is no BinOp for the operation %r"%op)

    def represent(self, *a,**kw):
        spec = environ.get_base_spec(*a, **kw)
        try:
            return environ._try_special_format(self, spec)
        except LookupError:
            pass
        left, right = self._format_operands(*a,**kw)
        symb = self.get_symbol(spec)
        return " ".join([left, symb, right])

    #all BinOps use their corrosponding function 
    def evaluate(self, *a,**kw):
        left = self.left.evaluate(*a,**kw)
        right= self.right.evaluate(*a,**kw)
        try:
            return self.func(left, right)
        except TypeError as e:
            raise e from environ.UserError

    def substitute(self, *a,**kw):
        left = self.left.substitute(*a,**kw)
        right = self.right.substitute(*a,**kw)
        if left is self.left and right is self.right:
            return self
        else:
            return BinOp(left, self.op, right)

#Add and Subtract always use the default
class Add(BinOp):
    __slots__ = ()
    symbol = "+"
    from operator import add as func
    
class Sub(BinOp):
    __slots__ = ()
    symbol = "-"
    from operator import sub as func


class Mult(BinOp):
    __slots__ = ()
    from operator import mul as func
    ### ! want to simplify multiplication with units to reduce number of lines basic initializations take up.
##    substitute = _mult_div_substitute
            
    def get_symbol(self, spec):
        left, right = self._format_operands("P")
        if spec=="L":
            symb = "\\cdot"
        else:
            symb = "*"
        if right.startswith("(") or left.endswith(")"):
            symb = ""
        return symb

class Div(BinOp):
    __slots__ = ()
    symbol = "/"
    from operator import truediv as func
##    substitute = _mult_div_substitute
    
    def _repr_latex_(self):
        num = self.left.represent(spec="L")
        den = self.right.represent(spec="L")
        return "\\frac{%s}{%s}"%(num,den)


class Pow(BinOp):
    __slots__ = ()
    symbol = "^"
    from operator import pow as func
    
    def _repr_latex_(self):
        base = self.format_arg(self.left, False)
        exp = self.right.represent(spec="L") #don't use format_arg here because exponent doesn't need brackets to indicate precedence
        return "%s^{%s}"%(base, exp)

    
class FloorDiv(Div):
    __slots__ = ()
    symbol = "//"
    from operator import floordiv as func
    
    def _repr_latex_(self):
        return r"\left \lfloor{%s}\right \rfloor"%str(self)

try:
    from operator import matmul
except ImportError:
    pass
else:
    class MatMult(BinOp):
        __slots__ = ()
        from operator import matmul as func
        
        def get_symbol(self, spec):
            if spec == "L":
                return "\\times "
            elif spec == "P":
                return "×"
            else:
                return "@"

######################### Uncertainties #################
try:
    from uncertainties import ufloat as _ufloat
except ImportError:
    class BitAnd(BinOp):
        symbol, func = "", lambda *a:None
        def __init__(*a,**kw):
            raise ModuleNotFoundError("cannot use +- unless uncertainties is installed")
else:
    class BitXor(BinOp):
        """used for uncertainty, uses uncertainties.ufloat as evaluation"""
        __slots__ = ()
        #if I ever do better handling with spec I will need to reimplement symbols
        def get_symbol(self, spec):
            if spec == "L":
                return "\\pm"
            elif spec == "P":
                return "±"
            else:
                return "+-"
        @staticmethod
        def func(value, error):
            if abs(error)>abs(value):
                from warnings import warn
                warn("the error is larger then the value, is that correct?")
            return _ufloat(value, error)
    
######################### Unary #################
        
@register_conv
class UnaryOp(ast.UnaryOp, Operation):
    __slots__ = ()
    _symbols = {ast.USub: "-", ast.UAdd: "+",
                ast.Invert: "~", ast.Not:"¬"}
    
    _funcs = {ast.USub:  operator.neg,
              ast.UAdd:  operator.pos,
              ast.Invert:operator.inv}
    try:
        import sympy
    except ImportError:
        _funcs[ast.Not] = operator.not_
    else:
        _funcs[ast.Not] = sympy.Not
        del sympy
    
    def represent(self, *a,**kw):
        symbol = self._symbols[type(self.op)]
        if isinstance(self.op, ast.Not) and environ.get_base_spec(*a,**kw) == "L":
            symbol = "\\neg"
        operand = self.format_arg(self.operand,False, *a,**kw)
        return symbol+operand
    
    def evaluate(self, *a,**kw):
        func = self._funcs[type(self.op)]
        operand = self.operand.evaluate(*a,**kw)
        try:
            return func(operand)
        except TypeError as e:
            raise e from environ.UserError
    def substitute(self, *a,**kw):
        operand = self.operand.substitute(*a,**kw)
        if operand is self.operand:
            return self
        else:
            return UnaryOp(self.op, self.operand)


