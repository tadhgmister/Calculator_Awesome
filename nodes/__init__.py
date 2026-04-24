__all__ = ['variables', 'constructs', 'operations', 'Node', 'register_conv', 'Parser']


import ast


_precedences = [
                [ast.Name, ast.Constant],
                [ast.Call, ast.Attribute, ast.Tuple, ast.List, ast.Subscript],
                [ast.Pow],
                [ast.UnaryOp],
                [ ast.Div, ast.FloorDiv], #div is given higher priority for when it is shown as a ratio (over multiple lines) it doesn't need brackets when paired with multiplication
                [ast.Mult, ast.MatMult],
                [ast.Add,ast.Sub],
                [ast.Compare],
                [ast.BoolOp],
                #the following don't really apply to precedence
                [ast.Module, ast.Expr, ast.Assign,
                 ast.Import, ast.ImportFrom, ast.alias,
                 ast.BitAnd, #used for uncertainty, always use brackets since BitAnd has much different precedence then people will expect
                 ast.RShift, #for logical implies, for now will always use brackets
                 NotImplemented #allow things to not implement precedence, so brackets will always be added when applicable.    
                 ]
               ]

precedence_reference = {}
#because it makes sense to make the list with top as high precedence we iterate over it in reverse
#so the last element has precedence of 0 and the top (first) has highest precedence.
for i, types in enumerate(reversed(_precedences)):
    for t in types:
        precedence_reference[t] = i

class Node():
    __slots__ = ()
    def _get_precedence(self):
        cls = type(self) #stupid classproperty not working >:(
        try:
            return precedence_reference[cls]
        except KeyError:
            return precedence_reference[cls._precedence_equivelent]

        
    @property
    def precedence(self):
        return self._get_precedence()



node_conversions = {}

def register_conv(cls):
    required_methods = ("represent","substitute", "evaluate")
    bases = cls.__bases__
    assert len(bases)==2 and issubclass(bases[1], Node), "can only directly register classes that use (<ast-node>, <Node>) as the bases"
    assert all(hasattr(cls, method) for method in required_methods), "{cls} did not implement all of {req}".format(cls=cls, req=required_methods)
    node_conversions[bases[0]] = cls
    if bases[0] in precedence_reference:
        precedence_reference[cls] = precedence_reference[bases[0]]
    return cls

##
#####do this after definitions so they can import register_conv and Node
from . import variables, constructs, operations, functions



__TEMPLATE = """

@register_conv
class NotImplemented(ast.None, Node):
    __slots__ = ()
    _precedence = NotImplemented

    def __format__(self, spec):
        NotImplemented
        
    def substitute(self):
        NotImplemented
        
    def evaluate(self):
        NotImplemented
        
"""
