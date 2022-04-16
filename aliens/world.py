from typing import List, Dict
from queue import deque
from dataclasses import dataclass, field

import numpy as np
from numba import jit

from aliens.items import Item
from aliens.components import PositionComponent
from aliens import colors
from aliens.symbols import *


class World:
    LAYERS = 2
    def __init__(self, size_x, size_y):
        self._init_cells(size_x, size_y)

    def _init_cells(self, size_x, size_y):
        self.cells = np.empty([size_x, size_y], dtype=Cell)
        
        for i in range(size_x):
            for j in range(size_y):
                self.cells[i, j] = Cell(i, j)
        
        for i in range(size_x):
            for j in range(size_y):
                ns = self.neighbors(i, j, size_x, size_y)
                for side, (ni, nj) in ns.items():
                    nb = self.cells[ni, nj]
                    self.cells[i, j].neighbors[side] = nb
                    setattr(self.cells[i, j], side, nb)

    def neighbors(self, x, y, size_x, size_y):
        sides = ['ul', 'u', 'ur', 'l', 'm', 'r', 'dl', 'd', 'dr']
        count = 0
        ns = {}
        for x2 in range(x-1, x+2):
            for y2 in range(y-1, y+2):
                side = sides[count]
                if (-1 < x < size_x and
                    -1 < y < size_y and
                    (x != x2 or y != y2) and
                    (0 <= x2 < size_x) and
                    (0 <= y2 < size_y)):
                    ns[side] = (x2, y2)
                count += 1
        return ns

    def add_item(self, x, y, item):
        self.cells[x, y].items.append(item)

    def remove_item(self, x, y, item):
        self.cells[x, y].items.remove(item)

    def move_item(self, x, y, newx, newy, item):        
        self.cells[x, y].items.remove(item)
        self.cells[newx, newy].items.append(item)  

    @property
    def walk_mask(self):
        mask = np.ones_like(self.cells, dtype=bool)
        size_x, size_y = self.cells.shape
        for i in range(size_x):
            for j in range(size_y):
                cell = self.cells[i, j]
                if cell.is_block_pass():
                    mask[i, j] = 0
        return mask

    @property
    def shape(self):
        return self.cells.shape

    def is_cell(self, x, y):
        return 0 <= x < self.cells.shape[0] and \
            0 <= y < self.cells.shape[1]


@dataclass(repr=False)
class Cell:
    x: int = -1
    y: int = -1
    neighbors: Dict[str, 'Cell'] = field(default_factory=dict)
    ul: 'Cell' = None
    u: 'Cell' = None
    ur: 'Cell' = None
    l: 'Cell' = None
    r: 'Cell' = None
    dl: 'Cell' = None
    d: 'Cell' = None
    dr: 'Cell' = None
    items: deque = field(default_factory=deque)

    def is_block_pass(self):
        for item in self.items:
            if item.physical.block_pass:
                return True
        return False

    def _cell_char_buffer(self):
        return np.full([World.LAYERS], SYMB_EMPTY, dtype=int)

    def _cell_color_buffer(self):
        return np.full([World.LAYERS], colors.transparent(), dtype=np.longlong) 

    def render(self):
        chars = self._cell_char_buffer()
        colors = self._cell_color_buffer()
        for item in self.items:
            if hasattr(item, 'render'):
                item.render.render(chars, colors)
        return chars, colors


if __name__ == '__main__':
    w = World(5, 3)