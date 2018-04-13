"""
minimal example of extension

implements reading numbers and doing addition
"""

import ast
from ..parser import Node


class Number(Node):
    def __init__(self, n):
        """
literal can be a ast.Num instance, a string that can be cast to a double
or other value"""
        if isinstance(n, ast.Num):
            self.val = n.n
        elif isinstance(n, str):
            self.val = float(n)
        else:
            self.val = n #assume it's just a literal value

    def evaluate(self):
        return self.val

    def represent(self):
        return str(self.val)


class Addition(Node):
    def __init__(self, left, right, op=None):
        if isinstance(left, Node) and isinstance(right, Node):
            self.left = left
            self.right = right
        else:
            raise TypeError("both operands must be Nodes")

    def evaluate(self):
        return self.left.evaluate() + self.right.evaluate()

    def represent(self):
        le = self.left.represent()
        ri = self.right.represent()
        return f"{le} + {ri}"


def update_class_map(class_map):
    class_map[ast.BinOp] = Addition
    class_map[ast.Num] = Number
    class_map[ast.Add] = ast.Add
