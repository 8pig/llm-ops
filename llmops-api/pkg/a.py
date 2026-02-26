from injector import inject, Injector


class A:
    name: str = "llmops"


@inject
class B:

    def __init__(self, a: A):
        self.a = a

    def print(self):
        print(self.a.name)




injector = Injector()
b = injector.get(B)
b.print()