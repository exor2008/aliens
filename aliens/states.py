from abc import ABC, abstractmethod
import numpy as np

from bearlibterminal import terminal

from aliens.symbols import *
from aliens import colors
from aliens.world import World
from aliens.items import Item
from aliens.rtenvironment import StoppableRealtimeEnvironment
from aliens.components import (
    PositionComponent,
    RenderComponent,
    CameraComponent,
    MarinesManagerComponent,
    PhysicalComponent,
    ActorComponent,
    HiveComponent,
)

class StateMashine:
    def __init__(self):
        self.store = {}
        self.state = InitScreen(self.store)
    
    def run(self):
        while self.state:
            self.state = self.state.run()


class State(ABC):
    def __init__(self, store):
        self.store = store
        self.handlers = InputHandlers({
            terminal.TK_CLOSE: self.on_exit,
            })
        self.screen_width = terminal.state(terminal.TK_WIDTH)
        self.screen_height = terminal.state(terminal.TK_HEIGHT)
        # self.setup()

    def on_exit(self):
        return

    # @abstractmethod
    # def setup(self):
    #     pass

    @abstractmethod
    def run(self):
        pass


class InitScreen(State):
    def __init__(self, store):
        super().__init__(store)
        self.render()
    # def setup(self):
    #     self.render()

    def render(self):
        terminal.clear()
        terminal.refresh()
        self.render_screen()
        self.render_logo()

        terminal.refresh()

    def render_screen(self):
        for i in range(self.screen_width):
            for j in range(self.screen_height):                
                [symbol] = random_tubes([1])
                terminal.color(colors.night_blue_bg())
                terminal.put(i, j, symbol.item())

    def render_logo(self):
        terminal.color(
            terminal.color_from_argb(
                255, 255, 255, 255))

        terminal.put_ext(18, 18, 5, 5, 36*16+1) # A
        terminal.put_ext(20, 18, 5, 5, 36*16+12) # L
        terminal.put_ext(22, 18, 5, 5, 36*16+9) # I
        terminal.put_ext(24, 18, 5, 5, 36*16+5) # E
        terminal.put_ext(26, 18, 5, 5, 36*16+14) # N
        

    def run(self):
        return MainMenuState(self.store, 25, 25, decorated=True)


class MenuState(State):
    def __init__(self, store, x, y, decorated=False):
        super().__init__(store)
        self.cur_row = 0

        self.x = x
        self.y = y
        self.decorated = decorated
        self.width = max(map(len, self.menu)) + 3

        self.height = len(self.menu) + 4
        
        self.handlers += InputHandlers({
            terminal.TK_ENTER: self.on_enter,
            terminal.TK_UP: self.on_up,
            terminal.TK_DOWN: self.on_down,
            })

        self.render(initial=True)

    def on_up(self):
        self.cur_row -= 1
        self.cur_row = len(self.menu) - 1 if self.cur_row < 0 else self.cur_row
        self.render()
        return self

    def on_down(self):
        self.cur_row += 1
        self.cur_row = 0 if self.cur_row >= len(self.menu) else self.cur_row
        self.render()
        return self

    def on_enter(self):
        callback = self.handlers[getattr(terminal, f'TK_{self.cur_row + 1}')]
        return callback()

    @property
    def menu(self):
        return [f'{i+1}.{item}' for i, item in enumerate(self.menu_list)]

    @property
    @abstractmethod
    def menu_list(self):
        pass

    def run(self):
        inpt = None
        if terminal.has_input():
            inpt = terminal.read()
            if callback := self.handlers.get(inpt):
                return callback()

        return self

    def render(self, initial=False):
        self.render_text()
        if self.decorated and initial:
            self.render_decor()
        terminal.refresh()

    def render_text(self):
        terminal.color(colors.white())
        for i, line in enumerate(self.menu):
            terminal.bkcolor(colors.black())
            terminal.color(colors.lt_gray())
            if i == self.cur_row:
                terminal.bkcolor(colors.predator_green_bg())
                terminal.color(colors.white())
            terminal.print(self.x + 2, self.y + i + 2, line)
        terminal.bkcolor(colors.black())
        terminal.color(colors.white())

    def render_decor(self):
        for i, symbol in enumerate(random_tubes([self.width])):
            terminal.color(colors.predator_green_bg())
            terminal.put(self.x + i, self.y, symbol.item())

        for i, symbol in enumerate(random_tubes([self.width])):
            terminal.color(colors.predator_green_bg())
            terminal.put(self.x + i, self.y + self.height - 1, symbol.item())

        for i, symbol in enumerate(random_tubes([self.height])):
            terminal.color(colors.predator_green_bg())
            terminal.put(self.x, self.y + i, symbol.item())

        for i, symbol in enumerate(random_tubes([self.height])):
            terminal.color(colors.predator_green_bg())
            terminal.put(self.x + self.width, self.y + i, symbol.item())


class MainMenuState(MenuState):
    def __init__(self, store, x, y, decorated=False):
        super().__init__(store, x, y, decorated)
        self.handlers += InputHandlers({
            terminal.TK_1: self.on_new_game,
            terminal.TK_2: self.on_exit,
            terminal.TK_ESCAPE: self.on_exit,
            })

    @property
    def menu_list(self):
        return ['New game', 'Quit']

    def on_new_game(self):
        return NewGameState(self.store)

    def on_exit(self):
        return


class EscMenuState(MenuState):
    def __init__(self, store, x, y, state, decorated=False):
        super().__init__(store, x, y, decorated)
        self.state = state
        self.handlers += InputHandlers({
            terminal.TK_1: self.on_continue,
            terminal.TK_2: self.on_exit,
            terminal.TK_ESCAPE: self.on_continue,
            })

    @property
    def menu_list(self):
        return ['Continue', 'Quit']        

    def on_continue(self):
        terminal.clear()
        return type(self.state)(self.store)

    def on_exit(self):
        return InitScreen(self.store)


class GameState(State):
    def __init__(self, store):
        super().__init__(store)
        self.handlers += InputHandlers({
            terminal.TK_ESCAPE: self.on_esc,
            })

    def render(self):
        self.camera.camera.update_terminal()

    def on_exit(self):
        return

    def on_esc(self):
        return EscMenuState(self.store, 25, 25, self, decorated=True)


class NewGameState(GameState):
    def __init__(self, store):
        super().__init__(store)

        terminal.clear()
        self._init_world()
        self._init_camera()
        self._init_floor()
        self._init_marines()
        self._init_hive()
        self._init_aliens()

    def run(self):
        return MarineControlState(self.store)

    def _init_world(self):
        self.world = World(200, 200)
        self.env = StoppableRealtimeEnvironment(strict=False)

        self.store['world'] = self.world
        self.store['env'] = self.env

    def _init_floor(self):
        size_x, size_y = self.world.shape
        for x in range(size_x):
            for y in range(size_y):
                floor = Item('Floor', self.world, self.env)
                floor.add_component(PositionComponent, self.camera, x, y)
                floor.add_component(RenderComponent, self.camera, 0, SYMB_FLOOR, colors.night_blue())
                floor.add_component(PhysicalComponent, self.camera, block_pass=False, block_sight=False)

    def _init_camera(self):
        self.camera = Item('Camera', self.world, self.env)
        self.camera.add_component(CameraComponent, 90, 45)
        self.camera.add_component(PositionComponent, self.camera, 0, 0)
        # self.camera.add_component(RenderComponent, 1, SYMB_CAMERA, colors.white())
        self.camera.add_component(PhysicalComponent, self.camera, block_pass=False, block_sight=False)
        self.camera.camera.update_requests.full()
        self.store['camera'] = self.camera

    def _init_marines(self):
        self.marines = Item('Marines', self.world, self.env)
        self.marines.add_component(MarinesManagerComponent, self.camera)

        self.marines.marinesmanager.spawn_marine(0, 0)
        self.marines.marinesmanager.next # init camera
        self.marines.marinesmanager.spawn_marine(103, 100)

        self.store['marines'] = self.marines

    def _init_hive(self):
        self.hive = Item('Hive', self.world, self.env)
        self.hive.add_component(HiveComponent, self.camera)
        self.hive.add_component(PositionComponent, self.camera, 80, 110)
        self.hive.add_component(RenderComponent, self.camera, 2, SYMB_HIVE, colors.light_blue())
        self.hive.add_component(ActorComponent, self.camera)
        self.hive.add_component(PhysicalComponent, self.camera, block_pass=True, block_sight=True)

        self.store['hive'] = self.hive

    def _init_aliens(self):
        self.hive = self.store['hive']
        hx, hy = self.hive.position.pos

        for x, y in np.random.randint(-3, 3, size=[4, 2]):
            self.hive.hive.spawn_alien(hx + x, hy + y)


class MarineControlState(GameState): # MarineControlGameState
    def __init__(self, store):
        super().__init__(store)
        self.camera = store['camera']
        self.env = store['env']
        self.marines = store['marines']
        self.render()

        self.handlers += InputHandlers({
            terminal.TK_MOUSE_LEFT | terminal.TK_KEY_RELEASED: self.on_click
            })

    def run(self):
        inpt = None

        if terminal.has_input():
            inpt = terminal.read()

            if callback := self.handlers.get(inpt):
                return callback()

        self.env.step()
        self.render()

        return self

    def on_click(self):
        x = terminal.state(terminal.TK_MOUSE_X)
        y = terminal.state(terminal.TK_MOUSE_Y)
        cx, cy = self.camera.camera.screen_to_cells(x, y)
        # print('click cell', cx, cy)

        marine = self.marines.marinesmanager.current
        marine.navigate.navigate(cx, cy)

        return self


class InputHandlers:
    def __init__(self, handlers):
        self.handlers = handlers

    def __add__(self, other):
        if not isinstance(other, InputHandlers):
            raise TypeError(
                f"unsupported operand type(s) for +: {type(self)} and {type(other)}")

        handlers = self.handlers.copy()
        handlers.update(other.handlers)
        return InputHandlers(handlers)

    def __getitem__(self, item):
        return self.handlers[item]

    def get(self, item):
        return self.handlers.get(item)