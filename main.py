# Driver

import pygame as pg

def main():

    running = True
    playing = True

    pg.init()
    pg.mixer.init()

    screen = pg.display.set_mode((0,0), pg.FULLSCREEN)
    clock = pg.time.Clock()

    while running:

        # start

        while playing:

            # game loop

if __name__ == '__main__':
    main()