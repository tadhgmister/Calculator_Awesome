# Tadhg's Awesome calculator

This program is intended primarily as a jupyter / IPython kernel
extension, it allows shorthand notation for common engineering
calculations and renders the equations, equations with values subbed
in, then the result for each line of calculation. All variables are
stored in the normal IPython namespace (except imports within the calc
cell magic described below). 

A typical example of a calculation might look like this (where %%calc is the jupyter "cell magic" notation)
```python
%%calc

from units import m,s

delta_t = (12+-2)s
delta_d = (50+-0.1)m

avg_speed = delta_d / delta_t

```

and the output would look like:

$$
\delta_{t} = \left( 12 \pm 2 \right)  s \\
\delta_{t} = \left( 12.0 \pm 2.0 \right)  s \\
\\
\delta_{d} = \left( 50 \pm 0.1 \right)  m \\
\delta_{d} = \left( 50.00 \pm 0.10 \right)  m \\
\\
avg\_speed = \frac{\delta_{d}}{\delta_{t}} \\
avg\_speed = \frac{\left( \left( 50.00 \pm 0.10 \right)\,\mathrm{m} \right)}{\left( \left( 12.0 \pm 2.0 \right)\,\mathrm{s} \right)} \\
avg\_speed = \left( 4.2 \pm 0.7 \right)\,\frac{\mathrm{m}}{\mathrm{s}}
$$

supported features include:
- normal arithmetic operations, assigning variables, calling functions
- variables with greek letter names are rendered as the appropriate symbol. underscores followed by a single letter (or greek name) are rendered as subscripts
- `^` means exponent (it is replaced by `**` before being interpreted as python notation.
- implicit multiplication like `2x` or `(a+b)x^2` are interpreted
  correctly although there are some cases that raise warnings that
  BEDMAS is not followed as function calls can't be fully
  differentiated from multiplication.
- `[1,2,3]` produces vectors which have exactly 3 coordinates
  (specifying 2 coordinates sets the z coordinate to 0). `[a,b]*[c,d]`
  performs dot product and `[a,b] @ [c,d]` performs cross product. (also the variables are rendered with arrow hats)
- `(1,2,3)` produce [numpy] arrays (if installed) although I have not tested this thoroughly
- `a +- b` produces ufloats from [uncertainties] package if installed. This does automatic error propogation.
  - uncertainties can be mixed with numpy arrrays and units but currently unsupported with vectors.
- if the [pint] package is installed then `from units import *` imports most common S.I. units which can be multiplied by other quantities
  - units can be mixed with vectors, numpy arrays or ufloats
- if the [sympy] package is installed `from symbolic import x,y,z` allows for symbolic variables to be imported.

## Getting started

to use the direct command line interface you can run the package as a module, for instance a minimum start would be:

    git clone https://github.com/tadhgmister/Calculator_Awesome.git
	python3 -m Calculator_Awesome
	
Alternatively from the folder containing this code you can use this statement regardless of the folder name:

    PYTHONPATH+=.. python3 -m ${PWD##*/}
	
(This is a viable way to run any python package with a `__main__.py` file.)

The other way to use it is to create a jupyter notebook in a context where this package is on the PYTHONPATH (the easiest way is to make the notebook in a folder which also contains the folder with this repo as the current working directory is always on the python path). Then you would do this near the top of the notebook:

    from Calculator_Awesome.IPythonMagics import initialize
	initialize(get_ipython())

This adds the `%%calc` [cell magic], so a cell can start with `%%calc` or `%%calc compact=True` and the rest of the cell will be interpreted as calculator syntax with the associated rendered output. Alternatively a single statement can be made by using `%calc` for instance:

    def func(x):
	    return 2*x + 3
	
	a = 5
	b = 1
	%calc func(a) func(b)
	print("ran inline 'magic')
	
Would print out:
    
	func(a) func(b)
	func((5)) func((1))
	65
	ran inline 'magic'
	


## Currently unsupported but potential extensions
Extensions I have considered but are currently unimplemented due to potentially confusing or conflicting syntax:
- using `f(x) := 2x - 4` syntax to define functions, `:=` doesn't support being the top level expression nor support subscript assignment so this wouldn't overlap with any existing python syntax but I haven't put in the effort since `:=` was released to figure out the appropriate string substitutions.
- implementing for loops or conditionals, have not seen enough cases to know what the desirable output would be.
- set union and intersection operations which use bitwise operators in python. for dictionaries and sets it may be desirable for intersection or union but I'd kind of prefer it throw an error for regular numbers unless you were sure it was useful in your specific context.
- any direct integration for plotting, mixing normal python code blocks to make plots with shorthand equations code blocks is often better in my experience. (previous versions had this and it was very clunky)

This calculator was made and tested with python 3.11, it relies on internal AST nodes which is possibly less stable than most python libraries. Any python operation that has not been implemented will throw an error indicating the AST node that was not implemented.

## technical details
The program heavily builds on existing logic in the `ast` module, there are string substitutions applied to the input as defined in `shorthand.py`, then it is passed through `ast.parse` and for each node in the tree it is replaced with a compatible node defined in the `nodes` folder. Nodes have 3 main functions: `represent` which returns a string representation, `substitute` which replaces variables with their values but returns the same kind of tree structure (which then calls `represent` to get a printable form) and `evaluate` which executes the statement. These directly correspond to the 3 lines each statement typically shows.

All methods seem to have arbitrary arguments as inputs but I don't think there is anywhere in the code that actually uses arguments or passes them. I suspect this is an artifact of before I was sure what arguments made sense and wanted to allow generic operations to forward those arguments down the tree. Mostly there are a few functions in `environ` which dictate the formatting spec such as using `L` for latex which renders well in jupyter.

### import quirks

Normally importing names overrides anything that existed before it, however imports in the calc mode work differently to support the case of `from symbolic import *` (which I now somewhat regret as that leads to typos being very hard to spot) and for imports to not directly overlap with IPython variables (which I also now regret as it means importing things in `calc` cells just doesn't make those names visible in python cells but the other way around works as you'd expect and that is confusing while not being super helpful) 

When names are imported like `import math` or `from units import s,m`, they are added to `environ.globals.maps[0]` (environ.globals is a ChainMap so updating it puts them in the first dictionary) which are shadowed by local variables. This means that doing:

    %%calc
	pi = 4
	from math import pi
	
	x = pi
	
will make `x == 4` since the local variable shadows all imported members.

using `from M import *` will add `M` to the `environ.globals` chainmap after the first dictionary for explicitly imported members but before any other star imports, so for example:

    %%calc
	x = 6
	from units import *, seconds
	from math import sin, cos
	from symbolic import *
	
will leave `x`, `seconds`, `sin`, and `cos` accessible but all other units which were imported by `*` are shadowed by sympy symbols. Also `x` will be stored in the IPython namespace and accessible in other cells while `seconds`, `sin`, `cos` are only accessible in `%%calc` cells. 

This is a silly design, I am aware. I will likely change it in the future as `from symbolic import *` and `from units import *` often cause more problems than they solve, but for now this is how it works.

[numpy]: https://pypi.org/project/numpy/
[uncertainties]: https://pypi.org/project/uncertainties/
[pint]: https://pypi.org/project/pint/
[sympy]: https://pypi.org/project/sympy/
[cell magic]: https://ipython.readthedocs.io/en/stable/interactive/magics.html
