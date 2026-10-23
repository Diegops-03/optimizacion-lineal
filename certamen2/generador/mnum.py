from fractions import Fraction as F
from functools import total_ordering

@total_ordering
class Mn:
    """a*M + b with M -> +infinity"""
    __slots__ = ('a', 'b')
    def __init__(self, a=0, b=0):
        if isinstance(a, Mn):
            self.a, self.b = a.a, a.b
        else:
            self.a, self.b = F(a), F(b)
    @staticmethod
    def of(x):
        if isinstance(x, Mn): return x
        if x == 'M': return Mn(1, 0)
        return Mn(0, x)
    def __add__(self, o): o = Mn.of(o); return Mn(self.a + o.a, self.b + o.b)
    __radd__ = __add__
    def __sub__(self, o): o = Mn.of(o); return Mn(self.a - o.a, self.b - o.b)
    def __rsub__(self, o): return Mn.of(o) - self
    def __neg__(self): return Mn(-self.a, -self.b)
    def __mul__(self, k):
        k = F(k); return Mn(self.a * k, self.b * k)
    __rmul__ = __mul__
    def __eq__(self, o):
        o = Mn.of(o); return self.a == o.a and self.b == o.b
    def __lt__(self, o):
        o = Mn.of(o); return (self.a, self.b) < (o.a, o.b)
    def __hash__(self): return hash((self.a, self.b))
    def isM(self): return self.a != 0
    def val(self, M=10**6): return float(self.a * M + self.b)
    def __str__(self):
        from core import fr
        if self.a == 0: return fr(self.b)
        s = ('' if self.a == 1 else ('−' if self.a == -1 else fr(self.a))) + 'M'
        if self.b == 0: return s
        return s + ('+' if self.b > 0 else '−') + fr(abs(self.b))
    __repr__ = __str__
