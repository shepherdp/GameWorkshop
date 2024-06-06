import pygame as pg

import matplotlib.pyplot as plt
import random

def draw_text(screen, text, size, color, pos):
    font = pg.font.SysFont(None, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(topleft=pos)
    screen.blit(text_surface, text_rect)

def load_sounds():

    chopping = pg.mixer.Sound("assets\\audio\\chopping.mp3")
    well = pg.mixer.Sound("assets\\audio\\well.mp3")
    quarry = pg.mixer.Sound("assets\\audio\\quarry.mp3")
    workbench = pg.mixer.Sound("assets\\audio\\workbench.mp3")
    wheatfield = pg.mixer.Sound("assets\\audio\\wheatfield.mp3")
    market = pg.mixer.Sound("assets\\audio\\market.mp3")
    road = pg.mixer.Sound("assets\\audio\\road.mp3")
    towncenter = pg.mixer.Sound("assets\\audio\\towncenter.mp3")
    house = pg.mixer.Sound("assets\\audio\\house.mp3")

    sounds = {'chopping': chopping,
              'well': well,
              'quarry': quarry,
              'workbench': workbench,
              'wheatfield': wheatfield,
              'market': market,
              'road': road,
              'towncenter': towncenter,
              'house': house}

    return sounds

def load_images():

    # world blocks
    rock = pg.image.load('assets\\graphics\\terrain\\rock.png').convert_alpha()
    tree = pg.image.load('assets\\graphics\\terrain\\tree.png').convert_alpha()
    grass1 = pg.image.load('assets\\graphics\\terrain\\grass1.png').convert_alpha()
    grass2 = pg.image.load('assets\\graphics\\terrain\\grass2.png').convert_alpha()
    grass3 = pg.image.load('assets\\graphics\\terrain\\grass3.png').convert_alpha()
    water = pg.image.load('assets\\graphics\\terrain\\water.png').convert_alpha()

    # buildings
    well = pg.image.load('assets\\graphics\\buildings\\well.png').convert_alpha()
    chopping = pg.image.load('assets\\graphics\\buildings\\choppingblock.png').convert_alpha()
    road = pg.image.load('assets\\graphics\\buildings\\road.png').convert_alpha()
    tc = pg.image.load('assets\\graphics\\buildings\\towncenter.png').convert_alpha()
    quarry = pg.image.load('assets\\graphics\\buildings\\quarry.png').convert_alpha()
    wheatfield = pg.image.load('assets\\graphics\\buildings\\wheatfield.png').convert_alpha()
    workbench = pg.image.load('assets\\graphics\\buildings\\workbench.png').convert_alpha()
    house = pg.image.load('assets\\graphics\\buildings\\house.png').convert_alpha()
    market = pg.image.load('assets\\graphics\\buildings\\market.png').convert_alpha()

    # icons
    water = pg.image.load('assets\\graphics\\icons\\water_icon.png').convert_alpha()
    stone = pg.image.load('assets\\graphics\\icons\\stone_icon.png').convert_alpha()
    wood = pg.image.load('assets\\graphics\\icons\\wood_icon.png').convert_alpha()
    wheat = pg.image.load('assets\\graphics\\icons\\wheat_icon.png').convert_alpha()
    simpletools = pg.image.load('assets\\graphics\\icons\\simpletools_icon.png').convert_alpha()

    # tech icons
    simpletools_tech_icon = pg.image.load('assets\\graphics\\icons\\simpletools_tech_icon.png').convert_alpha()
    agriculture_tech_icon = pg.image.load('assets\\graphics\\icons\\agriculture_icon.png').convert_alpha()

    # buttons
    deselect_button = pg.image.load('assets\\graphics\\buttons\\deselect_button.png').convert_alpha()
    select_button = pg.image.load('assets\\graphics\\buttons\\select_button.png').convert_alpha()
    delete_button = pg.image.load('assets\\graphics\\buttons\\delete_button.png').convert_alpha()

    beggar = pg.image.load('assets\\graphics\\characters\\beggar.png').convert_alpha()
    watercarrier = pg.image.load('assets\\graphics\\characters\\watercarrier.png').convert_alpha()
    woodcutter = pg.image.load('assets\\graphics\\characters\\woodcutter.png').convert_alpha()
    farmer = pg.image.load('assets\\graphics\\characters\\farmer.png').convert_alpha()
    quarryman = pg.image.load('assets\\graphics\\characters\\quarryman.png').convert_alpha()
    merchant = pg.image.load('assets\\graphics\\characters\\merchant.png').convert_alpha()



    images = {'rock': rock,
              'tree': tree,
              'well': well,
              'chopping': chopping,
              'road': road,
              'water': water,
              'towncenter': tc,
              'market': market,

              'beggar': beggar,
              'woodcutter': woodcutter,
              'watercarrier': watercarrier,
              'quarryman': quarryman,
              'farmer': farmer,
              'merchant': merchant,

              'water': water,
              'stone': stone,
              'wood': wood,
              'wheat': wheat,
              'simpletools': simpletools,

              'quarry': quarry,
              'wheatfield': wheatfield,
              'workbench': workbench,
              'grass1': grass1,
              'grass2': grass2,
              'grass3': grass3,
              'house': house,
              'simpletools_tech': simpletools_tech_icon,
              'agriculture': agriculture_tech_icon,
              'deselect_button': deselect_button,
              'select_button': select_button,
              'delete_button': delete_button
              }

    return images
