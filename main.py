# driver

import pygame as pg
from game.game import Game

def main():

    # running = True
    # playing = True

    pg.init()
    pg.mixer.init()

    # screen = pg.display.set_mode((0,0), pg.FULLSCREEN)
    screen = pg.display.set_mode((800, 600))
    clock = pg.time.Clock()

    game = Game(screen, clock)

    # while running:

        # start

        # while playing:

    game.run()

if __name__ == '__main__':
    main()