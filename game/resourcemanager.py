import pygame as pg

class ResourceManager:

    def __init__(self):

        self.resources = {'wood': 50,
                          'water': 50,
                          'stone': 50,
                          'gold': 50,
                          'wheat': 50}

        self.costs = {'well': {'wood': 5},
                      'chopping': {'wood': 3, 'water': 2},
                      'towncenter': {'wood': 10, 'water': 10},
                      'road': {'wood': 1},
                      'quarry': {'stone': 3},
                      'wheatfield': {'stone': 1, 'wood': 5, 'water': 10},
                      'house': {'wood': 2, 'stone': 2, 'water': 2}
                      }

    def apply_cost(self, bldg):
        for r, cost in self.costs[bldg].items():
            self.resources[r] -= cost

    def is_affordable(self, bldg):
        if bldg not in self.costs:
            return True
        for r, cost in self.costs[bldg].items():
            if self.resources[r] < cost:
                return False
        return True
