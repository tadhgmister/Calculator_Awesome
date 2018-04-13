"""
core service for plaintext
"""


from . import environment, parser
from .parser import withpython


def eval_line(expr):
    tree = parser.withpython.convert(expr, environment.class_map)
    print(tree.represent())
    print(tree.evaluate())
