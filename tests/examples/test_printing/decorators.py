# flake8: noqa
@fdec1
def function():
    pass


@fdec1
@fdec2(param=1)
def function2():
    pass


@cdec1(param=2)
@cdec2
class MyClass:
    pass
