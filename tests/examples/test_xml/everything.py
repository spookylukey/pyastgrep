# flake8:noqa
def function(arg):
    """Docstring"""
    assigned_string = "string_literal"
    assigned_int = 123
    assigned_float = 3.14
    assigned_bool = True


def function_kwarg(kwarg_arg=""):
    pass


def function_star_args(*args):
    pass


def function_star_kwargs(**kwargs):
    pass


def function_pos_kw_only(a, /, *, b):
    pass


def function_all(a, *args, b, c="", **kwargs):
    pass


class MyClass:
    pass


def function_ann(a: str, b: bool = False) -> str:
    c: int
    d: list[int] = [1]


ß = "☺"
