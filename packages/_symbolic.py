import types
try:
    import sympy
except ImportError:
    sympy = None
class Symbolic(types.ModuleType):
    def __getattr__(self, name):
        if not sympy:
            raise ModuleNotFoundError("cannot use symbolic unless sympy is installed")
        symb = sympy.Symbol(name)
        setattr(self, name, symb) #cache symbols so all variables are the same symbol.
        return symb
    

symbolic = Symbolic("symbolic")
