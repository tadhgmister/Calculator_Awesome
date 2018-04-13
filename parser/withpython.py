"""
Python AST implementation of the parser

For this implementation to work each syntax in extensions to define
python_ast_name which is assigned a string of the class in python's ast module

for example addition and subtraction is implemented with BinOp so you'd do

class Addition(Node):
    python_ast_name = "BinOp"

"""
import ast
from . import Node



def convert(expr:str, class_map):
    tree = ast.parse(expr, mode="eval").body
    return _translate_tree(tree, class_map)


def _translate_tree(ast_tree, class_map) -> Node:
    root_type = class_map[type(ast_tree)]
    ns = {}
    for name in type(ast_tree)._fields:
        value = getattr(ast_tree, name)
        if isinstance(value, ast.AST):
            value = _translate_tree(value, class_map)
        ns[name] = value

    return root_type(**ns)
