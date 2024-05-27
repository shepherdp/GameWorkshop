import pygame as pg

import matplotlib.pyplot as plt
import random

def draw_text(screen, text, size, color, pos):
    font = pg.font.SysFont(None, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(topleft=pos)
    screen.blit(text_surface, text_rect)

def load_images():

    # world blocks
    rock = pg.image.load('assets\\graphics\\terrain\\rock.png').convert_alpha()
    tree = pg.image.load('assets\\graphics\\terrain\\tree.png').convert_alpha()
    grass1 = pg.image.load('assets\\graphics\\terrain\\grass1.png').convert_alpha()
    grass2 = pg.image.load('assets\\graphics\\terrain\\grass2.png').convert_alpha()
    water = pg.image.load('assets\\graphics\\terrain\\water.png').convert_alpha()

    # buildings
    well = pg.image.load('assets\\graphics\\buildings\\well.png').convert_alpha()
    chopping = pg.image.load('assets\\graphics\\buildings\\choppingblock.png').convert_alpha()
    # block = pg.image.load('assets\\graphics\\buildings\\testblock.png').convert_alpha()
    road = pg.image.load('assets\\graphics\\buildings\\road.png').convert_alpha()
    tc = pg.image.load('assets\\graphics\\buildings\\towncenter.png').convert_alpha()
    quarry = pg.image.load('assets\\graphics\\buildings\\quarry.png').convert_alpha()
    wheatfield = pg.image.load('assets\\graphics\\buildings\\wheatfield.png').convert_alpha()
    workbench = pg.image.load('assets\\graphics\\buildings\\workbench.png').convert_alpha()
    house = pg.image.load('assets\\graphics\\buildings\\house.png').convert_alpha()

    # icons
    water_icon = pg.image.load('assets\\graphics\\icons\\water_icon.png').convert_alpha()
    stone_icon = pg.image.load('assets\\graphics\\icons\\stone_icon.png').convert_alpha()

    # tech icons
    simpletools_icon = pg.image.load('assets\\graphics\\icons\\simple_tools_icon.png').convert_alpha()
    agriculture_icon = pg.image.load('assets\\graphics\\icons\\agriculture_icon.png').convert_alpha()

    # buttons
    deselect_button = pg.image.load('assets\\graphics\\buttons\\deselect_button.png').convert_alpha()

    beggar = pg.image.load('assets\\graphics\\characters\\beggar.png').convert_alpha()
    watercarrier = pg.image.load('assets\\graphics\\characters\\watercarrier.png').convert_alpha()
    woodcutter = pg.image.load('assets\\graphics\\characters\\woodcutter.png').convert_alpha()
    farmer = pg.image.load('assets\\graphics\\characters\\farmer.png').convert_alpha()
    quarryman = pg.image.load('assets\\graphics\\characters\\quarryman.png').convert_alpha()


    images = {'rock': rock,
              'tree': tree,
              'well': well,
              'chopping': chopping,
              'road': road,
              'water': water,
              'towncenter': tc,

              'beggar': beggar,
              'woodcutter': woodcutter,
              'watercarrier': watercarrier,
              'quarryman': quarryman,
              'farmer': farmer,

              'quarry': quarry,
              'wheatfield': wheatfield,
              'workbench': workbench,
              'grass1': grass1,
              'grass2': grass2,
              'house': house,
              'water_icon': water_icon,
              'stone_icon': stone_icon,
              'simpletools': simpletools_icon,
              'agriculture': agriculture_icon,
              'deselect_button': deselect_button
              }

    return images
