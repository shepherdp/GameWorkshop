# Class that manages resources use, purchases, and sales in a town

from numpy import exp


class ResourceManager:

    price_ranges = {'wood': 10,
                    'stone': 16,
                    'water': 10,
                    'wheat': 12,
                    'simpletools': 50,
                    'coal': 30}
    max_prices = {'wood': 40,
                  'stone': 50,
                  'water': 35,
                  'wheat': 45,
                  'simpletools': 100,
                  'coal': 60}

    def __init__(self):

        self.resources = {'wood': 5000,
                          'water': 2000,
                          'stone': 5000,
                          'gold': 1000000,
                          'wheat': 5000,
                          'simpletools': 500,
                          'coal': 500}

        self.costs = {'well': {'wood': 5},
                      'temple': {'stone': 5, 'simpletools': 5},
                      'chopping': {'wood': 3, 'water': 2},
                      'towncenter': {'wood': 10, 'water': 10},
                      'road': {'wood': 1},
                      'quarry': {'stone': 3},
                      'wheatfield': {'stone': 1, 'wood': 5, 'water': 10},
                      'house': {'wood': 2, 'stone': 2, 'water': 2},
                      'workbench': {'wood': 4, 'stone': 1},
                      'market': {'wood': 10, 'stone': 10},
                      'coalmine': {'stone': 10},

                      'simpletools_tech': {'wood': 40, 'stone': 40},
                      'agriculture': {'wood': 50, 'simpletools': 20, 'water': 20}
                      }

        self.quantity_demanded = {'wood': 0,
                                  'wheat': 0,
                                  'water': 0,
                                  'stone': 0,
                                  'simpletools': 0,
                                  'coal': 0}

    def apply_cost(self, item):
        for r, cost in self.costs[item].items():
            self.resources[r] -= cost

    def is_affordable(self, item):
        if item not in self.costs:
            return True
        for r, cost in self.costs[item].items():
            if self.resources[r] < cost:
                return False
        return True

    def get_price(self, item, mode=0):
        price_range = self.price_ranges[item]
        max_price = self.max_prices[item]
        in_stock = self.resources[item]
        quantity_demanded = self.quantity_demanded[item]

        # mode 0 is town buying from someone
        if mode == 0:
            midpoint = quantity_demanded if quantity_demanded > 0 else 1
            k = 4 / midpoint + .01
        # mode 1 is town selling to someone
        elif mode == 1:
            midpoint = int(quantity_demanded * 1.5) if quantity_demanded > 0 else 1
            k = 8 / midpoint + .01
            max_price = int(max_price * 1.5)
            price_range = int(price_range * 1.5)

        return max_price - (1 / (1 + exp(-k * (in_stock - midpoint)))) * price_range
