from collections import OrderedDict

import numpy as np
import simpy

from aliens import colors
from aliens.symbols import *
from aliens.items import Item
from aliens.tasks import GoToTask, IdleTask

class Component:
    def __init__(self, item: Item):
        self.item = item
        self.world = item.world
        self.env = item.env


class PositionComponent(Component):
    def __init__(self, item: Item, x: int, y: int):
        super().__init__(item)
        self.x = x
        self.y = y
        self.world.add_item(x, y, item)

    def move(self, x, y):
        self.world.move_item(*self.pos, x, y, self.item)
        self.x = x
        self.y = y
        for item in self.item.items:
            item.position.move(x, y)

    @property
    def pos(self):
        return self.x, self.y


class RenderComponent(Component):
    def __init__(self, item: Item, layer: int, symbol: int, color: int):
        super().__init__(item)
        self.layer = layer
        self.symbol = symbol
        self._color = color

    def render(self, chars, colors):        
        chars[self.layer] = self.symbol
        colors[self.layer] = self.color

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        if not isinstance(value, int):
            raise ValueError("Color should be int, got {value} instead.")
        self._color = value


class CameraComponent(Component):
    def __init__(self, item: Item, width: int, height: int):
        super().__init__(item)
        self.width = width
        self.height = height

    # slow
    def render(self, width=None, height=None):
        width = width if width else self.width
        height = height if height else self.height

        x_from, x_to, y_from, y_to = self._frame(width, height)

        chars = np.full([width, height, self.world.LAYERS], SYMB_EMPTY, dtype=int)
        clrs = np.full([width, height, self.world.LAYERS], colors.transparent(), dtype=np.longlong)

        for x in np.arange(x_from, x_to):
            for y in np.arange(y_from, y_to):
                if self.world.is_cell(x, y):
                    cell_chars, cell_colors = self.world.cells[x, y].render()
                    chars[x - x_from, y - y_from] = cell_chars
                    clrs[x - x_from, y - y_from] = cell_colors

        return chars, clrs

    def _frame(self, width, height):
        x, y = self.item.position.pos

        x_from = x - width // 2
        x_to = x_from + width
        y_from = y - height // 2
        y_to = y_from + height

        return x_from, x_to, y_from, y_to

    def in_frame(self, x, y, width=None, height=None):
        width = width if width else self.width
        height = height if height else self.height

        x_from, x_to, y_from, y_to = self._frame(width, height)
        return x_from <= x < x_to and y_from <= y < y_to

    def screen_to_cells(self, x, y, width=None, height=None):
        width = width if width else self.width
        height = height if height else self.height

        x_from, x_to, y_from, y_to = self._frame(width, height)
        return x + x_from, y + y_from

    def cells_to_screen(self, x, y, width=None, height=None):
        width = width if width else self.width
        height = height if height else self.height

        x_from, x_to, y_from, y_to = self._frame(width, height)
        return x - x_from, y - y_from


class NavigateComponent(Component):
    def __init__(self, item: Item, speed: float = 1.0):
        super().__init__(item)
        self.task = None
        self.speed = speed
        self.proc = None

    def navigate(self, x, y):
        if self.proc and self.proc.is_alive:
            self.proc.interrupt('New goto task')
        self.proc = self.env.process(GoToTask(self.item, x, y, priority=0, preempt=True).execute())


class ActorComponent(Component):
    def __init__(self, item: Item):
        super().__init__(item)
        self.actor = simpy.PreemptiveResource(self.env, capacity=1)


class MarinesManagerComponent(Component):
    def __init__(self, item: Item, camera: Item):        
        super().__init__(item)
        self.camera = camera
        self.marines = OrderedDict()
        self._current = 0

    def spawn_marine(self, x, y):
        marine = Item('Marine', self.world, self.env)
        marine.add_component(PositionComponent, x, y)
        marine.add_component(RenderComponent, 1, SYMB_MARINE, colors.predator_green())
        marine.add_component(ActorComponent)
        marine.add_component(NavigateComponent, speed=100.0)
        marine.add_component(PhysicalComponent, block_pass=True, block_sight=True)

        self.env.process(IdleTask(marine, priority=10, preempt=False).execute())
        self.marines[marine.name] = marine

    @property
    def current(self):
        return list(self.marines.values())[self._current]

    @property
    def next(self):
        if self.camera in self.current.items:
            self.current.items.remove(self.camera)
        self._current += 1
        self._current = min(self._current, len(self.marines) - 1)
        self.current.items.append(self.camera)
        self.camera.position.move(*self.current.position.pos)

        return self.current

    @property
    def prev(self):
        if self.camera in self.current.items:
            self.current.items.remove(self.camera)
        self._current -= 1
        self._current = max(self._current, 0)
        self.current.items.append(self.camera)
        self.camera.position.move(*self.current.position.pos)

        return self.current


class PhysicalComponent(Component):
    def __init__(self, item: Item, block_pass, block_sight):        
        super().__init__(item)
        self.block_pass = block_pass
        self.block_sight = block_sight

# states items[components], task