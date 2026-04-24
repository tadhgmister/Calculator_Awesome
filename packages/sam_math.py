import math
NaN = float("nan")
class SamInt(int):
    def __new__(cls, num=0):
        if num<1:
            return small
        elif num >5:
            return big
        else:
            return super().__new__(cls, num)

    def __add__(a,b):
        return SamInt(int.__add__(a,b))
    def __radd__(a,b):
        return SamInt(int.__radd__(a,b))
    def __sub__(a,b):
        return SamInt(int.__sub__(a,b))
    def __rsub__(a,b):
        return SamInt(int.__rsub__(a,b))
    def __mul__(a,b):
        return SamInt(int.__mul__(a,b))
    def __rmul__(a,b):
        return SamInt(int.__rmul__(a,b))
    def __div__(a,b):
        return SamInt(int.__div__(a,b))
    def __rdiv__(a,b):
        return SamInt(int.__rdiv__(a,b))
    def __pow__(a,b):
        return SamInt(int.__pow__(a,b))
    def __rpow__(a,b):
        return SamInt(int.__rpow__(a,b))

class _Small:
    def __repr__(self):
        return "small"
    def __neg__(self):
        return NaN
    
    def __add__(self, other):
        return other #x + small == x
    __radd__ = __add__
    def __sub__(self, other):
        return small #small - x -> negative == small
    def __rsub__(self, other):
        return other #x - small == x
    def __mul__(self, other):
        if other is big: #small * big == NaN
            return NaN
        else: #small * x == small
            return self
    def __div__(self, other):
        if other is small: #small/small == NaN
            return NaN
        else: #small/x == small
            return self
    def __pow__(self, other):
        if other is small: #small ** small == NaN ??
            return NaN
        else: #small ** x == small
            return self
    def __rpow__(exp, base):
        return small #x**small == small
    
small = _Small()

class _Big:
    def __repr__(self):
        return "big"
    def __neg__(self):
        return small
    
    def __add__(self, other):
        return big #x + big == big
    __radd__ = __add__
    def __sub__(self, other):
        if other is big:
            return NaN #big - big -> NaN
        else:
            return big #big - x -> big
    def __rsub__(self, other):
        return small #x - big == small
    def __mul__(self, other):
        if other is small: #big * small == NaN
            return NaN
        else: #big * x == big
            return self
    def __div__(self, other):
        if other is big: #big/big == NaN
            return NaN
        else: #big/x == big
            return self
    def __pow__(self, other):
        if other is small: #big ** small == NaN ??
            return NaN
        else: #big ** x == big
            return self
big = _Big()


def sin(x):return small
def cos(x):return small
def tan(x):return NaN

def factorial(x):
    if x is small or x == 1:
        return SamInt(1)
    elif x == 2:
        return 2
    else:
        return big

def integrate(expr, var): return expr + var

e = pi = SamInt(3)
