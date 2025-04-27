import math
import numpy as np
import random

# constants for entities to be mapped on the grid
EMPTY = 0
AGENT = 1
PLANET = 2
METEOR = 3
SPACE_STATION = 4
NEBULA = 5
RADIATION_ZONE = 6
UNEXPLORED = 7
END = 8
class SpaceEnvironment:
    def __init__(self, grid=(20,20)):
        self.grid =grid
        self.grid = np.full(grid, 0)

        # entity containers
        self.planets = []
        self.meteors = []
        self.space_stations = []
        self.nebulas = []
        self.radiation_zones = []

        # game info
        self.timestep = 0
        self.starting_position = None
        self.end_position = None
        
        # goals
        self.resource_goals = {}
        self.mapping_goal_percentage = 0.0

        pass

    def intialize_env(self, agent_position=None,
                      end_position=None,
                      num_planets=4,
                      num_meteors=5,
                      num_space_stations=2,
                      num_nebulas=2,
                      num_radiation_zones=2,
                      mapping_goal_percentage=70.0,
                      resource_goals=None):
        # reset env
        self.grid = np.full(self.grid_size, EMPTY, dtype=int)
        self.planets = []
        self.meteors = []
        self.space_stations = []
        self.nebulas = []
        self.radiation_zones = []
        self.timestep = 0

        # goals
        self.mapping_goal_percentage = mapping_goal_percentage
        self.resource_goals = resource_goals or {"Water":10, "Minerals": 15, "Oxygen": 5}

        # track occupied positions
        occupied_positions = set()

        # agent position 
        if agent_position:
            self.starting_position = agent_position
        else:
            start_row = random.randint(0, self.grid[0]-1)
            start_col = random.randint(0, self.grid[1]-1)
            self.starting_position = (start_row, start_col)
        # add agent to grid
        occupied_positions.add(self.starting_position)
        self.grid[self.starting_position] = AGENT

        # end position
        if end_position:
            self.end_position = end_position
        else:
            self.end_position = self.get_ranom_empty_position(occupied_positions)
        # add end position to grid
        occupied_positions.add(self.end_position)
        self.grid[self.end_position] = END

        # Generating entities
        # generating planets
        resources = ["Water", "Oxygen", "Minerals"]
        for i in range(num_planets):
            position = self.get_ranom_empty_position(occupied_positions)
            planet = {
                "type":PLANET,
                "position":position,
                "resource_type":random.choice(resources),
                "resource_amount":random.randint(5,20)
            }
            self.planets.append(planet)
            occupied_positions.add(position)
            self.grid[position] = PLANET
        
        # generating meteors
        for i in range(num_meteors):
            position = self.get_ranom_empty_position(occupied_positions)
            # random movements for 5 timesteps
            directions= ["UP", "DOWN", "LEFT", "RIGHT"]
            pattern = [random.choice(directions) for j in range(5)]
            meteor= {
                "type":METEOR,
                "position":position,
                "damage":random.randint(5,15),
                "movement_pattern": pattern,
                "pattern_i":0
            }
            self.meteors.append(meteor)
            occupied_positions.add(position)
            self.grid[position] = METEOR

        # generating nebulas
        for i in range(num_nebulas):
            position = self.get_ranom_empty_position(occupied_positions)
            nebula = {
                "type":NEBULA,
                "position":position,
                "sensor_reduction":1
            }
            self.nebulas.append(nebula)
            occupied_positions.add(position)
            self.grid[position] = NEBULA
        
        # generating radiation zone
        for i in range(num_radiation_zones):
            position = self.get_ranom_empty_position(occupied_positions)
            radiation_zone = {
                "type":RADIATION_ZONE,
                "position":position,
                "damage":2
            }
            self.radiation_zones.append(radiation_zone)
            occupied_positions.add(position)
            self.grid[position] = RADIATION_ZONE
        
        # generating space stations
        for i in range(num_space_stations):
            position = self.get_ranom_empty_position(occupied_positions)
            space_station = {
                "type":SPACE_STATION,
                "position":position,
                "refuel_amount":70
            }
            self.space_stations.append(space_station)
            occupied_positions.add(position)
            self.grid[position] = SPACE_STATION
        
        return
    
    def get_ranom_empty_position(self, occupied_positions):
        while True:
            r = random.randint(0, self.grid[0]-1)
            c = random.randint(0, self.grid[1]-1)
            if (r,c) not in occupied_positions:
                return (r,c)

    def update(self):
        #move everything and add timestep
        pass
    def sense(self):
        #sense environement
        pass
    def actions(self):
        #return allowable actions
        pass