import types
try:
    import pint, pint.errors
    ureg = pint.UnitRegistry()
except ImportError:
    ureg = None
else:
    ureg.define("percent = 0.01count = %")

class Unit_module(types.ModuleType):
    if ureg:
        epsilon_0 = 8.85e-12 *ureg.C**2/(ureg.N*ureg.m**2)
        percent = ureg.percent
    def __getattr__(self, attr):
        if not ureg:
            raise ModuleNotFoundError("cannot use units unless pint is installed")
        try:
            return getattr(ureg, attr)
        except pint.errors.UndefinedUnitError as e:
            raise AttributeError(attr) from e

units = Unit_module("units")
