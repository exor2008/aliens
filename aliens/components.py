from collections import OrderedDict

import tcod
import simpy
import numpy as np
from bearlibterminal import terminal

from aliens import colors
from aliens.symbols import *
from aliens.items import Item
from aliens.tasks import GoToTask, IdleTask
from aliens.terminal_updates import UpdateRequests

class BaseComponent:
    def __init__(self, item: Item):
        self.item = item
        self.world = item.world
        self.env = item.env


class Component(BaseComponent):
    def __init__(self, item: Item, camera: Item):
        super().__init__(item)
        self.camera = camera


class PositionComponent(Component):
    def __init__(self, item: Item, camera: Item, x: int, y: int):
        super().__init__(item, camera)
        self.x = x
        self.y = y
        self.world.add_item(x, y, item)

    def move(self, x, y):
        self.camera.camera.update_requests.move_item(self.item, x, y)
        self.world.move_item(*self.pos, x, y, self.item)
        self.look(self.item, x, y)
        
        self.x = x
        self.y = y

        for item in self.item.items:
            item.position.move(x, y)

    def look(self, item, x, y):
        if hasattr(item, 'direction'):
            item.direction.look(x, y)

    @property
    def pos(self):
        return self.x, self.y


class DirectionComponent(Component):
    directions = {
            (-1, -1): 'dl',
            (-1, 0): 'l',
            (-1, 1): 'ul',
            (0, 1): 'u',
            (1, 1): 'ur',
            (1, 0): 'r',
            (1, -1): 'dr',
            (0, -1): 'd',
        }

    @property
    def masks(self):
        return {
            'dl': lambda arr: self.down_left(arr),
            'l': lambda arr: self.left(arr),
            'ul': lambda arr: self.up_left(arr),
            'u': lambda arr: self.up(arr),
            'ur': lambda arr: self.up_right(arr),
            'r': lambda arr: self.right(arr),
            'dr': lambda arr: self.down_right(arr),
            'd': lambda arr: self.down(arr),
        }

    def __init__(self, item: Item, camera: Item, direction: str = 'u'):
        super().__init__(item, camera)
        self.width = terminal.state(terminal.TK_WIDTH)
        self.height = terminal.state(terminal.TK_HEIGHT)
        self.offset = - ((self.width - self.height) // 2 + 2)
        if self.offset > 0:
            self.offset += 1
        self.direction = direction

    def look(self, x, y):
        ix, iy = self.item.position.pos
        look_x = np.clip(x - ix, -1, 1)
        look_y = np.clip(y - iy, -1, 1)
        self.direction = self.directions[(look_x, look_y)]

    def mask(self, arr):
        return self.masks[self.direction](arr)
        
    def up(self, arr):
        mask = arr.astype(bool)
        to = int(round(mask.shape[1] / 2)) + 1 - self.shift[1]
        mask[:, :to] = False
        return mask
        
    def down(self, arr):
        mask = arr.astype(bool)
        from_ = int(round(mask.shape[1] / 2)) - self.shift[1]
        mask[:, from_:] = False
        return mask
            
    def left(self, arr):
        mask = arr.astype(bool)
        from_ = int(round(mask.shape[0] / 2)) + self.shift[0]
        mask[from_:] = False
        return mask
        
    def right(self, arr):
        mask = arr.astype(bool)
        to = int(round(mask.shape[0] / 2)) + 1 + self.shift[0]
        mask[:to] = False
        return mask

    def down_right(self, arr):
        mask = arr.astype(bool)
        offset = self.offset - (self.shift[0] + self.shift[1])
        visible = np.tri(*arr.shape, offset, dtype=bool)
        mask[~visible] = False
        return mask

    def down_left(self, arr):
        mask = arr.astype(bool)
        offset = self.offset - (self.shift[1] - self.shift[0])
        visible = np.flipud(np.tri(*arr.shape, offset + 1, dtype=bool))
        mask[~visible] = False
        return mask

    def up_right(self, arr):
        mask = arr.astype(bool)
        offset = self.offset - (self.shift[0] - self.shift[1])
        visible = np.fliplr(np.tri(*arr.shape, offset, dtype=bool))
        mask[~visible] = False
        return mask

    def up_left(self, arr):
        mask = arr.astype(bool)
        offset = self.offset + self.shift[0] + self.shift[1] + 1
        visible = np.flipud(np.fliplr(np.tri(*arr.shape, offset, dtype=bool)))
        mask[~visible] = False
        return mask

    @property
    def shift(self):
        cx, cy = self.camera.camera.cells_to_screen(*self.camera.position.pos)
        x, y = self.camera.camera.cells_to_screen(*self.item.position.pos)
        return x - cx, cy - y

    @property
    def shift_diag(self):
        cx, cy = self.camera.camera.cells_to_screen(*self.camera.position.pos)
        x, y = self.camera.camera.cells_to_screen(*self.item.position.pos)
        return x - cx, -(y - cy)


class FieldOfViewComponent(Component):
    def __init__(self, item: Item, camera: Item, radius: int):
        super().__init__(item, camera)
        self.radius = radius

    def fov(self, mask):
        x_screen, y_screen = self.camera.camera.cells_to_screen(*self.item.position.pos)
        return tcod.map.compute_fov(mask, [x_screen, y_screen], radius=self.radius)


class RenderComponent(Component):
    directions = {
        'dl': SYMB_DL,
        'l': SYMB_L,
        'ul': SYMB_UL,
        'u': SYMB_U,
        'ur': SYMB_UR,
        'r': SYMB_R,
        'dr': SYMB_DR,
        'd': SYMB_D,
        }

    def __init__(self, item: Item, camera: Item, layer: int, symbol: int, color: int):
        super().__init__(item, camera)
        self.layer = layer
        self.symbol = symbol
        self._color = color

    def render(self, chars, clrs):
        chars[self.layer] = self.symbol
        clrs[self.layer] = self.color
        if hasattr(self.item, 'direction'):
            chars[self.layer + 1] = self.render_direction()
            clrs[self.layer + 1] = colors.white()

    def render_direction(self):
        return self.directions[self.item.direction.direction]

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        if not isinstance(value, int):
            raise ValueError("Color should be int, got {value} instead.")
        self._color = value


class CameraComponent(BaseComponent):
    def __init__(self, item: Item, width: int, height: int):
        super().__init__(item)
        self.width = width
        self.height = height
        self.need_update = None
        self.chars = None
        self.colors = None
        self.update_requests = UpdateRequests(self.world, self)

    def update_terminal(self, observers):
        if updater := self.update_requests.get_updater():
            updater.update(observers)

    def _frame(self, width, height):        
        x, y = self.item.position.pos

        x_from = x - int(round(width / 2))
        x_to = x_from + width
        y_from = y - int(round(height / 2))
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
        return x + x_from, height - y + y_from - 1

    def cells_to_screen(self, x, y, width=None, height=None):
        width = width if width else self.width
        height = height if height else self.height

        x_from, x_to, y_from, y_to = self._frame(width, height)
        return x - x_from, y - y_from

    def follow(self, item):
        if self.item.owner:
            self.item.owner.remove_item(self.item)
        self.item.owner = item
        self.item.owner.add_item(self.item)
        self.item.position.move(*item.position.pos)


class NavigateComponent(Component):
    def __init__(self, item: Item, camera: Item, speed: float = 1.0):
        super().__init__(item, camera)
        self.task = None
        self.speed = speed
        self.proc = None

    def navigate(self, x, y):
        if self.proc and self.proc.is_alive:
            self.proc.interrupt('New goto task')
        self.proc = self.env.process(GoToTask(self.item, x, y, priority=0, preempt=True).execute())


class ActorComponent(Component):
    def __init__(self, item: Item, camera: Item):
        super().__init__(item, camera)
        self.actor = simpy.PreemptiveResource(self.env, capacity=1)


class MarinesManagerComponent(Component):
    def __init__(self, item: Item, camera: Item):        
        super().__init__(item, camera)
        self.marines = OrderedDict()
        self._current = 0

    def spawn_marine(self, x, y, direction='u'):
        marine = Item('Marine', self.world, self.env)
        marine.add_component(PositionComponent, self.camera, x, y)
        marine.add_component(RenderComponent, self.camera, 1, SYMB_MARINE, colors.predator_green())
        marine.add_component(ActorComponent, self.camera)
        marine.add_component(DirectionComponent, self.camera, direction=direction)
        marine.add_component(NavigateComponent, self.camera, speed=100.0)
        marine.add_component(PhysicalComponent, self.camera, block_pass=True, block_sight=True)
        marine.add_component(FieldOfViewComponent, self.camera, radius=100)

        self.env.process(IdleTask(marine, priority=10, preempt=False).execute())
        self.marines[marine.name] = marine
        return marine

    @property
    def current(self):
        return list(self.marines.values())[self._current]

    @property
    def next(self):
        self._current += 1
        self._current = min(self._current, len(self.marines) - 1)
        self.camera.camera.follow(self.current)

        return self.current

    @property
    def prev(self):
        self._current -= 1
        self._current = max(self._current, 0)
        self.camera.camera.follow(self.current)

        return self.current


class HiveComponent(Component):
    def __init__(self, item: Item, camera: Item):        
        super().__init__(item, camera)
        self.aliens = OrderedDict()
        self.mass = 0

    def spawn_alien(self, x, y):
        alien = Item('Alien', self.world, self.env)
        alien.add_component(PositionComponent, self.camera, x, y)
        alien.add_component(RenderComponent, self.camera, 1, SYMB_ALIEN, colors.light_blue())
        alien.add_component(ActorComponent, self.camera)
        alien.add_component(DirectionComponent, self.camera)
        alien.add_component(NavigateComponent, self.camera, speed=100.0)
        alien.add_component(PhysicalComponent, self.camera, block_pass=True, block_sight=True)
        alien.add_component(FieldOfViewComponent, self.camera, radius=45)

        self.env.process(IdleTask(alien, priority=10, preempt=False).execute())
        self.aliens[alien.name] = alien
        return alien


class PhysicalComponent(Component):
    def __init__(self, item: Item, camera: Item, block_pass, block_sight):        
        super().__init__(item, camera)
        self.block_pass = block_pass
        self.block_sight = block_sight

# states items[components], task