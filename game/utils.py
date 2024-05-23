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
    rock = pg.image.load('assets\\graphics\\rock.png').convert_alpha()
    tree = pg.image.load('assets\\graphics\\tree.png').convert_alpha()
    grass1 = pg.image.load('assets\\graphics\\grass1.png').convert_alpha()
    grass2 = pg.image.load('assets\\graphics\\grass2.png').convert_alpha()

    # buildings
    well = pg.image.load('assets\\graphics\\well.png').convert_alpha()
    chopping = pg.image.load('assets\\graphics\\choppingblock.png').convert_alpha()
    block = pg.image.load('assets\\graphics\\testblock.png').convert_alpha()
    road = pg.image.load('assets\\graphics\\road.png').convert_alpha()
    water = pg.image.load('assets\\graphics\\water.png').convert_alpha()
    tc = pg.image.load('assets\\graphics\\towncenter.png').convert_alpha()
    worker = pg.image.load('assets\\graphics\\worker.png').convert_alpha()
    quarry = pg.image.load('assets\\graphics\\quarry.png').convert_alpha()
    wheatfield = pg.image.load('assets\\graphics\\wheatfield.png').convert_alpha()
    house = pg.image.load('assets\\graphics\\house.png').convert_alpha()

    # icons
    water_icon = pg.image.load('assets\\graphics\\icons\\water_icon.png').convert_alpha()


    images = {'rock': rock,
              'tree': tree,
              'well': well,
              'chopping': chopping,
              'block': block,
              'road': road,
              'water': water,
              'towncenter': tc,
              'worker': worker,
              'quarry': quarry,
              'wheatfield': wheatfield,
              'grass1': grass1,
              'grass2': grass2,
              'house': house,
              'water_icon': water_icon
              }

    return images
