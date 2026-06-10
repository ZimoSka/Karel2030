# -*- coding: utf-8 -*-
"""Karel core – základné typy: Direction a výnimky."""
from enum import Enum

# =========================================================================
# SVET  /  WORLD MODEL
# =========================================================================

class Direction(Enum):
    NORTH = 0
    EAST  = 1
    SOUTH = 2
    WEST  = 3
    def left(self):     return Direction((self.value-1)%4)
    def right(self):    return Direction((self.value+1)%4)
    def opposite(self): return Direction((self.value+2)%4)
    def to_str(self):
        return {Direction.NORTH:'N',Direction.SOUTH:'S',
                Direction.EAST:'E', Direction.WEST:'W'}[self]
    @staticmethod
    def from_str(s):
        return {'N':Direction.NORTH,'S':Direction.SOUTH,
                'E':Direction.EAST,'W':Direction.WEST,
                'NORTH':Direction.NORTH,'SOUTH':Direction.SOUTH,
                'EAST':Direction.EAST,'WEST':Direction.WEST}[s.upper()]

class KarelError(Exception): pass
class KarelStop(Exception): pass   # tiché zastavenie (napr. narazenie do steny)
class KarelBudget(Exception):      # vyčerpaný rozpočet pohybu (kroky/otočenia)
    def __init__(self, kind): self.kind = kind   # 'steps' | 'turns'
class KarelLimit(Exception):       # bezpečnostný strop: nekonečný cyklus / hlboká rekurzia
    def __init__(self, kind): self.kind = kind   # 'loop' | 'recursion'


