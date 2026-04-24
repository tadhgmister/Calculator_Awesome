from operator import itemgetter as _itemgetter
import collections.abc
import math
import numbers

import ast

VALID_SCALARS = [int,float, numbers.Number]

class Vector(object):
    __unit = False
    def __init__(self,x,y=None,z=None):
        if isinstance(x, collections.abc.Iterable) and y is None and z is None:
            x,y,z = x
        #! TO DO: add numeric checks to initializer
        self.x = x
        self.y = y
        self.z = z

    @property
    def _i(self):
        """returns the three components as a tuple, used for iteration in methods"""
        return self.x, self.y, self.z

    @classmethod
    def _repr_coef(cls, coef,spec=""):
        """returns a representation of a coeficient in front of a unit vector"""
        if coef==-1:
            return "-"
        elif coef== 1:
            return "+"
        elif coef == 0:
            return "+0"
        elif spec and not isinstance(coef, (int,float)):
            #if there was a spec explicitly defined use it in any other case
            return format(coef, spec)
        elif isinstance(coef, float):
            return format(coef, "+.2f")
        else:
            return format(coef, "+")

    @classmethod
    def _repr_unit_var(cls, var_name, spec="", unit=True):
        """returns a representation of a unit i,j or k.  (only really exists for latex support)"""
        if "L" in spec:
            if unit:
                hat_vec = "hat"
            else:
                hat_vec = "vec"
            return "\\%s{%s}"%(hat_vec, var_name)
        else:
            return var_name
        
    def __repr_var__(self, name, spec):
        return self._repr_unit_var(name, spec, self.__unit)
    def __format__(self,spec):
        if "L" in spec:
            return latex_repr_column_vector(self)
        s = ""
        terms = 3 #how many terms were there
        for n,d in zip(self._i, "ijk"):
            if n==0:
                terms-=1
                continue
            s+=self._repr_coef(n, spec)+self._repr_unit_var(d,spec)
        s = s.strip(" +")
        if terms==0:
            if "L" in spec:
                return "\\vec{0}"
            elif "P" in spec:
                return "0\u20D1" #'0⃑'
            else:
                return "0"
        elif terms==1:
            return s
        else:
            #more then one term, add parenthases
            if "L" in spec:
                return "\\left( %s \\right)"%s
            else:
                return "(%s)"%s
        
        
    def __repr__(self):
        return "Vector({0.x!r}, {0.y!r}, {0.z!r})".format(self)
    
    def __str__(self):
        return format(self,"")

    

     #this should be the default 
    def repr(self, environ):
        return format(self, environ.spec)

    

    def __neg__(self):
        return Vector(-a for a in self._i)
    def __abs__(self):
        return math.sqrt(sum(a**2 for a in self._i))


    def __add__(self,other):
        if isinstance(other,Vector):
            return Vector(a+b for a,b in zip(self._i,other._i))
        return NotImplemented
    def __sub__(self,other):
        if isinstance(other,Vector):
            return Vector(a-b for a,b in zip(self._i,other._i))
        return NotImplemented
        
    def dot(self,other):
        "dot product, default behaviour when multiplying vectors together"
        return sum(a*b for a,b in zip(self._i,other._i))
    def cross(a,b):
        "cross product, default behaviour of matmul (a @ b) for vectors"
        return Vector(a.y*b.z - b.y*a.z,
                      a.z*b.x - b.z*a.x,
                      a.x*b.y - b.x*a.y)
    
    def proj(self,other):
        """projects one vector onto another"""
        return self.dot(other)/abs(other)**2 * other

    def __mul__(self,other):
        if isinstance(other,Vector):
            return self.dot(other)
        elif isinstance(other, VALID_SCALARS):
            return Vector(a*other for a in self._i)
        return NotImplemented
    
    def __rmul__(self,other):
        if isinstance(other, VALID_SCALARS):
            return Vector(other*a for a in self._i)
        return NotImplemented
    def __div__(self,other):
        if isinstance(other, VALID_SCALARS):
            return Vector(a/other for a in self._i)
        return NotImplemented
    __truediv__ = __div__
    
    def __matmul__(self,other):
        if isinstance(other, Vector):
            return self.cross(other)
        return NotImplemented


    def as_unit(self):
        """unit vector, self/abs(self)"""
        result = self/abs(self)
        result.__unit = True #used only by __repr_var__
        return result

    def sub(self, environ):
        return self
    def eval(self, environ):
        return self
    order = ast.Module
    def precedence(self):
        terms = sum(a!=0 for a in self._i)
        if terms==1:
            #if the non-zero one is 1 then it is one of (i, j, k) so treat it like a number
            if any(a==1 for a in self._i):
                return ast.Num
            else:
                #treat like multiplication
                return ast.Mult
        #otherwise have lower precedence then addition
        return ast.Module
##

def latex_repr_column_vector(v:Vector):
    return r"\begin{{bmatrix}}{v.x}\\{v.y}\\{v.z}\end{{bmatrix}}".format(v=v)


def azimuth_altitude(azimuth, altitude):
    return rot(altitude, rot(azimuth, i, j), k)

def rot(reference, angle, to):
    assert reference.dot(to) == 0, "can only call rot on orthagonal vectors"
    return math.cos(angle)*reference + math.sin(angle) * to


i = Vector(x=1,y=0,z=0)
j = Vector(x=0,y=1,z=0)
k = Vector(x=0,y=0,z=1)

i._Vector__unit = j._Vector__unit = k._Vector__unit = True
