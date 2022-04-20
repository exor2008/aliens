from abc import ABC, abstractmethod

import numpy as np
from numba import jit
from bearlibterminal import terminal

from aliens.symbols import *
from aliens import colors

class TerminalUpdate(ABC):
    def __init__(self, world, camera):
        self.world = world
        self.camera = camera

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def render(self):
        pass


class FullTerminalUpdate(TerminalUpdate):
    def render(self):
        width = self.camera.width
        height = self.camera.height

        x_from, x_to, y_from, y_to = self.camera._frame(width, height)

        chars = np.full([width, height, self.world.LAYERS], SYMB_EMPTY, dtype=int)
        clrs = np.full([width, height, self.world.LAYERS], colors.transparent(), dtype=np.longlong)

        fov = self.fov()

        for x in np.arange(x_from, x_to):
            for y in np.arange(y_from, y_to):
                x_screen, y_screen = self.camera.cells_to_screen(x, y)
                if self.world.is_cell(x, y) and fov[x_screen, y_screen]:
                    cell_chars, cell_colors = self.world.cells[x, y].render()
                    chars[x_screen, y_screen] = cell_chars
                    clrs[x_screen, y_screen] = cell_colors

        return chars, clrs

    def update(self):
        chars, colors = self.render()

        terminal.clear()
        terminal.composition(True)
        size_x, size_y, _ = chars.shape

        chars_colors = np.dstack([chars, colors])
        for x, y, char, color in fast_iterate(chars_colors):
            terminal.color(color)
            terminal.put(x, y, char)
        terminal.composition(False)
        terminal.refresh()

        self.need_update = False

    def fov(self):
        if owner := self.camera.item.owner:
            if hasattr(owner, 'fieldofview'):
                mask = self.world.sight_mask(self.camera)
                return owner.fieldofview.fov(mask)
        return np.ones([self.camera.width, self.camera.height])
        


class UpdateRequests:
    def __init__(self, world, camera):
        self.world = world
        self.camera = camera
        self.reset()

    def full(self):
        self.full_update = True

    def move_item(self, item, x, y):
        old_x, old_y = item.position.pos
        if self.camera.in_frame(x, y) or self.camera.in_frame(old_x, old_y):
            self.full_update = True

    def reset(self):
        self.full_update = False

    def get_updater(self):
        if self.full_update:
            self.reset()
            return FullTerminalUpdate(self.world, self.camera)


@jit(nopython=True)
def fast_iterate(chars_colors):
    size_x, size_y, _ = chars_colors.shape

    for x in range(size_x):
        for y, y_flip in zip(range(size_y), range(size_y-1, -1, -1)):
            for char, color in chars_colors[x, y_flip].reshape(2, -1).T:
                yield x, y, char, color