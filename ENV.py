import math
import numpy as np
import random
# Imoprtant for agent code!!
# agent_state is the dic {"position":x,"fuel":x,"health":x, "collected_resources":x, "covered_map_percentage":x,"explored_cells":x }
# position is tuple row and col (1,2)
# both health and fuel are int
# collected_resources is the dic {"water":x, "minerals": x, "oxygen": x} where the values are int
# covered_map_percentage is float
# explored_cells is set of every explored cell (1,2)

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
        self.grid_size = grid  
        self.grid = np.full(grid, 0)
        self.occupied_positions = set()

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


    def initialize_env(self, agent_position=None,
                      end_position=None,
                      num_planets=4,
                      num_meteors=5,
                      num_space_stations=2,
                      num_nebulas=2,
                      num_radiation_zones=2,
                      mapping_goal_percentage=70.0,
                      resource_goals=None):
        # reset env
        self.grid = np.full(self.grid.shape, EMPTY, dtype=int)
        self.planets = []
        self.meteors = []
        self.space_stations = []
        self.nebulas = []
        self.radiation_zones = []
        self.timestep = 0

        # goals
        self.mapping_goal_percentage = mapping_goal_percentage
        self.resource_goals = resource_goals or {"water":10, "minerals": 15, "oxygen": 5}

        # reset occupied positions
        self.occupied_positions = set()

        # agent position 
        if agent_position:
            self.starting_position = agent_position
        else:
            start_row = random.randint(0, self.grid_size[0]-1)
            start_col = random.randint(0, self.grid_size[1]-1)
            self.starting_position = (start_row, start_col)

        # add agent to grid
        self.occupied_positions.add(self.starting_position)
        self.grid[self.starting_position] = AGENT

        # end position
        if end_position:
            self.end_position = end_position
        else:
            self.end_position = self.get_ranom_empty_position()
        
        # add end position to grid
        self.occupied_positions.add(self.end_position)
        self.grid[self.end_position] = END

        # Generating entities
        # generating planets
        resources = ["water", "oxygen", "minerals"]
        for i in range(num_planets):
            position = self.get_ranom_empty_position()
            planet = {
                "type":PLANET,
                "position":position,
                "resource_type":random.choice(resources),
                "resource_amount":random.randint(5,20)
            }
            self.planets.append(planet)
            self.occupied_positions.add(position)
            self.grid[position] = PLANET
        
        # generating meteors
        for i in range(num_meteors):
            position = self.get_ranom_empty_position()
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
            self.occupied_positions.add(position)
            self.grid[position] = METEOR

        # generating nebulas
        for i in range(num_nebulas):
            position = self.get_ranom_empty_position()
            nebula = {
                "type":NEBULA,
                "position":position,
                "sensor_reduction":1
            }
            self.nebulas.append(nebula)
            self.occupied_positions.add(position)
            self.grid[position] = NEBULA
        
        # generating radiation zone
        for i in range(num_radiation_zones):
            position = self.get_ranom_empty_position()
            radiation_zone = {
                "type":RADIATION_ZONE,
                "position":position,
                "damage":2
            }
            self.radiation_zones.append(radiation_zone)
            self.occupied_positions.add(position)
            self.grid[position] = RADIATION_ZONE
        
        # generating space stations
        for i in range(num_space_stations):
            position = self.get_ranom_empty_position()
            space_station = {
                "type":SPACE_STATION,
                "position":position,
                "refuel_amount":70
            }
            self.space_stations.append(space_station)
            self.occupied_positions.add(position)
            self.grid[position] = SPACE_STATION
        
        return
    
    def get_ranom_empty_position(self):
        while True:
            r = random.randint(0, self.grid_size[0]-1)
            c = random.randint(0, self.grid_size[1]-1)
            if (r,c) not in self.occupied_positions:
                return (r,c)

    # ACTION FUNCTIONS

    # get allowable actions
    def actions(self, agent_state):
        agent_position = agent_state["position"]

        # scan is always allowed
        allowed_actions=["SCAN"]

        # if health or fuel are 0
        if agent_state["health"] <= 0: return allowed_actions
        if agent_state["fuel"] <= 0 and agent_position != PLANET:return allowed_actions
        if agent_state["fuel"] <= 0 and agent_position == PLANET:
            allowed_actions.append("DOCK")
            return allowed_actions
        
        # add allowed moves
        for direction in ["UP", "DOWN", "LEFT", "RIGHT"]:
            new_position = self.get_new_position(agent_position, direction)
            if self.is_valid_position(new_position):
                allowed_actions.append(direction)

        # check if collect is allowed
        for planet in self.planets:    
            if agent_position == planet["position"]:
                allowed_actions.append("COLLECT")

        # check if dock id allowed
        for station in self.space_stations:    
            if agent_position == station["position"]:
                allowed_actions.append("DOCK")

        return allowed_actions
    
    def get_new_position(self, position, direction):
        row, col = position
        if direction == "UP":
            return (row - 1, col)
        elif direction == "DOWN":
            return (row + 1, col)
        elif direction == "LEFT":
            return (row, col - 1)
        elif direction == "RIGHT":
            return (row, col + 1)
        return position

    def is_valid_position(self, position):
        row, col = position
        return 0 <= row < self.grid_size[0] and 0 <= col < self.grid_size[1]
    
    # result function
    # will return the dic {"agent_state":agent_state, "percepts":percepts}
    # agent_state is defined above
    # percepts is a list of dictionaries for each entity in every cell {"position": pos, "entity_type": entity_type}
    # entity_type is int from the entity constants defined above 
    # if action is SCAN percepts will store scan result else it will be empty
    def do_action(self, agent_state, action):
    
        percepts = []

        # check if action is allowed
        if action not in self.actions(agent_state): 
            return {"agent_state":agent_state, "percepts":percepts}
        
        agent_health = agent_state["health"]
        agent_position=agent_state["position"]
        agent_fuel = agent_state["fuel"]

        # if action is move
        if action in ["UP", "DOWN", "LEFT", "RIGHT"]:
            # empty current position
            if agent_position in self.occupied_positions:
                self.occupied_positions.remove(agent_position)
            self.grid[agent_position] = EMPTY
            # move to new position
            agent_position = self.get_new_position(agent_position, action)
            # update grid with new agent position
            self.grid[agent_position] = AGENT
            self.occupied_positions.add(agent_position)

            agent_state["explored_cells"].add(agent_position)
            total_cells = self.grid.shape[0] * self.grid.shape[1]
            agent_state["covered_map_percentage"] = (len(agent_state["explored_cells"]) / total_cells) * 100

            # consume fuel
            agent_fuel -=1
            
            # check for effects of new position

            # meteors 
            for meteor in self.meteors:
                if meteor["position"] == agent_position:
                    agent_health -= meteor["damage"]
            # radiation zones
            for radiation_zone in self.radiation_zones:
                if radiation_zone["position"] == agent_position:
                    agent_health -= radiation_zone["damage"]

        elif action == "SCAN":
            sensor_range = 3            

            # check if in nebula
            for nebula in self.nebulas:
                if agent_position == nebula["position"]:
                    sensor_range -= nebula["sensor_reduction"]
            
            # check if scan is in bounds
            row, col = agent_position
            min_row = max(0, row - sensor_range)
            max_row = min(self.grid.shape[0] - 1, row + sensor_range)
            min_col = max(0, col - sensor_range)
            max_col = min(self.grid.shape[1] - 1, col + sensor_range)
            # 
            for r in range(min_row, max_row + 1):
                for c in range(min_col, max_col + 1):
                    pos = (r, c)
                    entity_type = self.grid[pos]

                    # add scanned cells
                    percept = {"position": pos, "entity_type": entity_type}
                    percepts.append(percept)
                    
                    # mark cell as explored
                    agent_state["explored_cells"].add(pos)
            # update covered map percentage
            total_cells = self.grid.shape[0] * self.grid.shape[1]
            agent_state["covered_map_percentage"] = (len(agent_state["explored_cells"]) / total_cells) * 100

        elif action == "COLLECT":
            planet=None
            # find which planet agent is on
            for p in self.planets:
                if p["position"] == agent_position:
                    planet = p
                    break
            
            if planet is not None:
                # collect resource
                agent_state["collected_resources"][planet["resource_type"]] += planet["resource_amount"]
                planet["resource_amount"] = 0

        elif action == "DOCK":
            
            station = None
            # find which station agent is on
            for s in self.space_stations:
                if s["position"] == agent_position:
                    station = s
            if station is not None:
                # refuel
                agent_fuel += station["refuel_amount"]
                if agent_fuel > 100: 
                    agent_fuel = 100
                
        agent_state["health"] = agent_health
        agent_state["position"] = agent_position
        agent_state["fuel"] = agent_fuel

        return {"agent_state":agent_state, "percepts":percepts}
    
    # UPDATE ENVIRONMENT FUNCTIONS

    def update_env(self, agent_state):
        self.timestep +=1
        # update env
        self.move_meteors(agent_state)
        self.add_nebula()

    def move_meteors(self, agent_state):
        agent_position = agent_state["position"]
        directions= ["UP", "DOWN", "LEFT", "RIGHT"]
        for meteor in self.meteors:
            # random direction
            direction = random.choice(directions)
            new_pos = self.get_new_position(meteor["position"], direction)
            
            if self.is_valid_position(new_pos) and (new_pos not in self.occupied_positions or new_pos == agent_position):
                # make old position emtpy
                if meteor["position"] in self.occupied_positions:
                    self.occupied_positions.remove(meteor["position"])
                self.grid[meteor["position"]] = EMPTY
                # update position
                meteor["position"] = new_pos
                self.occupied_positions.add(new_pos)

                # check collision
                if new_pos == agent_position:
                    agent_state["health"] -= meteor["damage"]
    
    def add_nebula(self):
        # 2% chance to generate a nebula
        if random.random() < 0.02:
            position = self.get_ranom_empty_position()
            nebula = {
                "type":NEBULA,
                "position":position,
                "sensor_reduction":1
            }
            self.grid[position] = NEBULA
            self.nebulas.append(nebula)
            self.occupied_positions.add(position)

    # GOAL FUNCTION
    # returns dic {is_game_over:true, is_map_covered:true, is_resources_met:false}
    def is_game_over(self, agent_state):
        is_over = False
        is_map_covered = False
        is_resources_met = True

        # is game over ?
        if agent_state["health"] <= 0: is_over = True
        if agent_state["fuel"] <= 0 and self.grid[agent_state["position"]] != SPACE_STATION: is_over = True
        if agent_state["position"] == self.end_position: is_over = True

        # is map covered?
        if agent_state["covered_map_percentage"] >= self.mapping_goal_percentage:
            is_map_covered = True

        # is resources goal met?
        for resource_type, goal_amount in self.resource_goals.items():
            if agent_state["collected_resources"][resource_type] < goal_amount:
                is_resources_met = False
        
        return {"is_game_over":is_over,"is_map_covered":is_map_covered, "is_resources_met": is_resources_met}