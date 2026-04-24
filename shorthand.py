
__all__ = ['update_string']

import re
import keyword
_normal_keywords = {"True", "False", "None", #these aren't really useful but I'd rather they be builtin then identifiers
                    "import", "from", "as", #used for importing
                    "and", "or", "not", "is", #logical operators
                    "for", "in", #generator expressions
                   }

keywords_allowed_as_identifiers = set(keyword.kwlist) - _normal_keywords

class REGEX():
    int = r"[+-]?\s*\d+"
    numeric = fr"{int}(?:\.\d+)?(?:e{int})?"
    variable = r"[a-zA-Z_]\w*\b"

    term = fr"(?P<coef>{numeric})?(?P<var>{variable})?"
    term_with_end_paren = "(?P<paren>[\\)\\]][ \\t]*)?"+term

    keyword_exception = "\\b("+"|".join(keywords_allowed_as_identifiers)+")\\b"

def substitute_alternate_spelling(s):
    #use ^ as exponent operator, note that it is important this happens beore custom_ops as it uses the ^ symbol
    s = s.replace("^","**") 
    #escape python keywords that are allowed as identifiers
    def escaped_identifier(match):
        return match.group()+"_"
    s = re.sub(REGEX.keyword_exception, escaped_identifier, s)
    #let % be used as the variable "percent" or part of a variable
    s=  s.replace("%","percent")
    return s

def _add_mul(match):
    """replace function for re.sub(REGEX.term_with_end_paren, _add_mul, <s>)"""
    groups= ("paren","coef","var")
    strings = [match.group(g) for g in groups]
    while None in strings:
        strings.remove(None)
    return "*".join(strings)
    
def add_implicit_multiplication(s):
    """adds * between terms (4x, (x)N) that would be implicitly multiplied"""
    s = re.sub(REGEX.term_with_end_paren, _add_mul, s)
    return s

def replace_custom_ops(s):
    if "^" in s:
        raise NotImplementedError("bitwise ^ is used internally for +- and is therefore unimplementable")
    for plus_minus in ("+-", "+/-", "±"):
        s = s.replace(plus_minus, "^")
    return s
def update_string(s):
    """updates an input string with all shorthand substitutions"""
    s = substitute_alternate_spelling(s)
    s = add_implicit_multiplication(s)
    s = replace_custom_ops(s)
    return s
