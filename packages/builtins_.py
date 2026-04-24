from builtins import *



def locals():
    from .. import environ
    return environ.locals
def globals():
    from .. import environ
    return environ.globals

def exec(code):
    from ..parsing import parse_expression
    node = parse_expression(code, mode="exec")
    return node.evaluate() #should be None

def eval(code):
    from ..parsing import parse_expression
    node = parse_expression(code, mode="eval")
    return node.evaluate()
