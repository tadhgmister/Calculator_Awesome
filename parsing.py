from . import nodes, shorthand, environ
import ast
def make_node_conversions(node):
    """recursively converts an ast node to use the alternate versions"""
    new_type = nodes.node_conversions.get(type(node))
    if new_type is None:
        if isinstance(node, ast.AST) and not isinstance(node, nodes.Node) and node._fields:
            raise NotImplementedError("ast %r hasn't been implemented"%type(node))
        return node
    elif new_type is type(node):
        #if a conversion is 
        return node
    else:
        try:
            return new_type(*conv_fields(node))
        except TypeError:
            print("FAILING ON MAKING %r NODE"%new_type)
            raise

def conv_fields(node):
    """generates the arguments to a converted ast node (recursive with make_node_conversions)"""
    for arg_name in node._fields:
        arg = getattr(node, arg_name)
        if isinstance(arg, list):
            yield [make_node_conversions(a) for a in arg]
        else:
            yield make_node_conversions(arg)               


def parse_expression(string, mode="exec"):
    edited_str = shorthand.update_string(string)
    tree = ast.parse(edited_str, mode=mode)
    return make_node_conversions(tree)

def step_eval(node, *, repeat_subs=False, debug=False):
    yield node
    if not repeat_subs:
        #only one substitution please.
        node = node.substitute()
        yield node
        return node.evaluate()
    #else: keep going
    new = None
    while True:
        new = node.substitute()
        if new is not node:
            yield new
            node = new
        else:
            break
    return node.evaluate()

def step_strings(node, **kw):
    steps = step_eval(node, **kw)
    try:
        while True:
            yield next(steps).represent()
    except StopIteration as e:
        if e.value is not None:
            yield environ.format(e.value)

### Can't figure out how this function would work since
### the method of displaying would vary depending on platform (terminal / iPython)
##def exec(text_or_node):
##    if isinstance(text_or_node, str):
##        body = parse_expression(text_or_node)
##    elif isinstance(text_or_node, ast.Module):
##        body = text_or_node.body
##    else:
##        body = [text_or_node]
##    for node in body:
##        yield from step_eval(node)

