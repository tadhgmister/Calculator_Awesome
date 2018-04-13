

from .core_minimal import eval_line


for line in iter(input, ""):
    eval_line(line)
    
