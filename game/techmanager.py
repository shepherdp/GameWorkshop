# Class that manages technology upgrades and unlocks for a town
import pygame as pg

BLDG_PREREQS = {'chopping': [],
                'well': [],
                'quarry': [],
                'wheatfield': ['agriculture'],
                'workbench': ['simpletools'],
                'towncenter': [],
                'house': [],
                'road': [],
                'market': []}

TECH_PREREQS = {'simpletools': [],
                'agriculture': ['simpletools']}

TECH_TIMES = {'simpletools': 10000 // 10,
              'agriculture': 14000 // 10}

class TechManager:

    def __init__(self):

        self.building_unlock_status = {key: False for key in BLDG_PREREQS}
        self.tech_unlock_status = {key: False for key in TECH_PREREQS}
        self.current_research = {}
        self.technologies = []
        self.update_unlock_status()
        self.researchcooldowns = {}

    def start_research(self, techname):
        self.current_research[techname] = 0
        self.researchcooldowns[techname] = pg.time.get_ticks()

    def increment_research(self, techname):
        if self.current_research[techname] == 90:
            self.technologies.append(techname)
            self.update_unlock_status()
            return True
        else:
            self.current_research[techname] += 10
            return False

    def update_unlock_status(self):
        for key in self.building_unlock_status:
            # self.building_unlock_status[key] = True
            if all([i in self.technologies for i in BLDG_PREREQS[key]]):
                self.building_unlock_status[key] = True
        for key in self.tech_unlock_status:
            # self.tech_unlock_status[key] = True
            if key in self.technologies:
                self.tech_unlock_status[key] = False
            elif all([i in self.technologies for i in TECH_PREREQS[key]]):
                self.tech_unlock_status[key] = True

    def update_research_progress(self):
        finished = []
        for tech in self.current_research:
            now = pg.time.get_ticks()
            if now - self.researchcooldowns[tech] > TECH_TIMES[tech]:
                f = self.increment_research(tech)
                if f:
                    finished.append(tech)
                else:
                    self.researchcooldowns[tech] = now
        for tech in finished:
            del self.researchcooldowns[tech]
            del self.current_research[tech]