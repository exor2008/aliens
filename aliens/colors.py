import numpy as np
from bearlibterminal import terminal

def night_blue_bg():
    shade = np.random.randint(30, 180)
    alpha = np.random.randint(0, 80)
    return terminal.color_from_argb(
        alpha, 0, 52, 92 + np.random.randint(-15, 15))

def night_blue():
    shade = np.random.randint(30, 180)
    alpha = np.random.randint(100, 250)
    return terminal.color_from_argb(
        alpha, 0, 52, 92 + np.random.randint(-15, 15))

def light_blue_bg():
    shade = np.random.randint(30, 180)
    alpha = np.random.randint(0, 80)
    return terminal.color_from_argb(
        alpha, 9, 113, 166 + np.random.randint(-15, 15))

def light_blue():
    shade = np.random.randint(30, 180)
    alpha = np.random.randint(100, 250)
    return terminal.color_from_argb(
        alpha, 9, 113, 166 + np.random.randint(-15, 15))

def red():
    return terminal.color_from_argb(255, 255, 0, 0)

def white():
    return terminal.color_from_argb(255, 255, 255, 255)

def black():
    return terminal.color_from_argb(255, 0, 0, 0)

def lt_gray():
    return terminal.color_from_argb(255, 200, 200, 200)

def gray():
    return terminal.color_from_argb(255, 128, 128, 128)

def dk_gray():
    return terminal.color_from_argb(255, 80, 80, 80)

def red():
    return terminal.color_from_argb(255, 255, 0, 0)

def predator_green():
    shade = np.random.randint(10, 50)
    green = np.random.randint(180, 255)
    alpha = np.random.randint(180, 255)
    return terminal.color_from_argb(
        alpha, 
        shade, 
        green,
        shade,)

def predator_green_bg():
    shade = np.random.randint(10, 50)
    green = np.random.randint(180, 255)
    alpha = np.random.randint(100, 200)
    return terminal.color_from_argb(
        alpha, 
        shade, 
        green,
        shade,)

def transparent():
    return terminal.color_from_argb(0, 0, 0, 0)
