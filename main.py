
from pathlib import Path

import simpy
from bearlibterminal import terminal

from aliens.states import StateMashine
from aliens.components import PositionComponent, RenderComponent, CameraComponent
from aliens.symbols import *
import aliens.colors


RESOURCES_PATH = Path(r'aliens', 'resources', 'fonts')
FONT_PATH = RESOURCES_PATH / 'alienleagueexpand.ttf'
ATLAS_PATH = RESOURCES_PATH / 'aliens.png'

def slow_proc(env):
    count = 0
    while True:
        yield env.timeout(1)
        print(f'another step {count}')
        count += 1


if __name__ == '__main__':
    # env = StoppableRealtimeEnvironment(strict=False)
    # proc = env.process(slow_proc(env))

    terminal.open()

    terminal.set('window: size=90x45')
    terminal.set(f'font: {FONT_PATH}, size=16x16')
    terminal.set(f'0x100: {ATLAS_PATH}, size=16x16');
    terminal.set(f'0x200: {FONT_PATH}, size=64x64')
    terminal.set('input.filter=[keyboard, mouse+]')

    sm = StateMashine()
    sm.run()
    
    # terminal.composition(True)
    # white = terminal.color_from_argb(255,255,255,255)
    # transparent = terminal.color_from_argb(100,255,0,0)
    
    # terminal.bkcolor(terminal.color_from_argb(255,0,255,0))
    # terminal.color(white)
    # terminal.put(9, 10, ord('a'))
    # terminal.put(10, 10, SYMB_FLOOR)
    # terminal.put(11, 10, SYMB_FLOOR)

    # terminal.color(white)
    # terminal.put(10, 10, SYMB_MARINE)

    # terminal.color(terminal.color_from_argb(255,255,255,255))
    # terminal.put(10, 10, 16*16)

    # terminal.color(terminal.color_from_argb(0,0,0,0))
    # terminal.put(10, 10, 31 * 16 + 15)
    # terminal.refresh()

    # terminal.put(1, 1, 0xff)
    # for i in range(16):
    #     for j in range(32):
    #         terminal.put(i, j, 16*31)
            # print(i, j, i+j*16)
        # print()
    # terminal.refresh()

    # stop = stop_prev = False
    # while True:
    #     inpt = None
    #     if terminal.has_input():
    #         inpt = terminal.read()

    #     if inpt == terminal.TK_SPACE:
    #         stop = not stop
        # if inpt == terminal.TK_CLOSE:
        #     print(inpt, terminal.TK_CLOSE)
        #     break

    #     if stop != stop_prev and stop:
    #         env.stop()
    #         print('stop')
    #     if stop != stop_prev and not stop:
    #         env.resume()
    #         print('continued')

    #     env.step()
    #     stop_prev = stop
    
    # print('exit')
    terminal.close()
