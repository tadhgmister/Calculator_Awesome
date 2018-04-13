
"""
bare minimum for the environment

It will need to be changed at some point to be object oriented but
initially this is sufficient
"""

loaded_extensions = ["sample"]

from .extensions import sample

class_map = {}
sample.update_class_map(class_map)

