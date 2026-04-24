import ast

from .. import environ
from . import Node, register_conv
from . import variables
from .operations import Operation

@register_conv
class Call(ast.Call, Operation):
    __slots__ = ()

    def represent(self, *a,**kw):
        args = [arg.represent(*a,**kw) for arg in self.args]
        args.extend(k.represent(*a, **kw) for k in self.keywords)
        if isinstance(self.func, variables.Value):
            func_obj = self.func.value
        elif isinstance(self.func, variables.Variable) and self.func.id in environ.globals:
            func_obj = environ.globals[self.func.id]
        else:
            func_obj = None
        if hasattr(func_obj, "__repr_func__"):
            return func_obj.__repr_func__(*args)
        if isinstance(self.func, ast.Name):
            func = self.func.represent(*a,**kw)
        else:
            func = self.format_arg(self.func, False, *a,**kw)
        return func + environ.add_parens(", ".join(args), force=True)

    def substitute(self, *a,**kw):
        subbed_args = [arg.substitute(*a,**kw) for arg in self.args]
        subbed_keywords = [arg.substitute(*a,**kw) for arg in self.keywords]
        #in simplest case this will return the name unchanged
        #if the call is really multiplication this is absolutely necessary
        func = self.func.substitute(*a,**kw)
        if (func is self.func
            and all((new is old) for new,old in zip(subbed_args, self.args))
            and all((new is old) for new,old in zip(subbed_keywords, self.keywords))):
            return self #no substitutions were made
        else:
            return Call(func, subbed_args, subbed_keywords)

    def evaluate(self, *a,**kw):
        func = self.func.evaluate(*a,**kw)
        args = [arg.evaluate(*a,**kw) for arg in self.args]
        keywords = {arg.arg:arg.value.evaluate(*a,**kw) for arg in self.keywords}
        if callable(func):
            return func(*args, **keywords)
        elif len(self.args)==1 and len(keywords)==0:
            [a] = args
            try:
                result = func * a
            except TypeError as e:
                raise e from environ.UserError
            else:
                from warnings import warn
                warn("function call evaluated as multiplication, BEDMAS may not have been followed")
                return result
        else:
            msg = ("function is not callable\n"
                   "(and can't be multiplication with multiple arguments)")
            raise TypeError(msg) from environ.UserError
    


@register_conv
class keyword(ast.keyword, Node):
    def represent(self, *a, **kw):
        return "{0.arg}={val}".format(self, val=self.value.represent(*a, **kw))
    def substitute(self, *a, **kw):
        val = self.value.substitute(*a, **kw)
        if val is self.value:
            return self
        else:
            return keyword(self.arg, val)

    def evaluate(self,*a, **kw):
        raise TypeError("keywords cannot be evaluated?")
