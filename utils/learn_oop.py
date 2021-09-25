class A:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    @property
    def a(self):
        return self.a

    @a.setter
    def a(self, value):
        self.a = value

    @classmethod
    def sum(cls):
        return cls

    @staticmethod
    def stat_sum():
        return
