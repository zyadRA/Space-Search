import heapq
import random
import math
from collections import deque

class Agent:
    def __init__(self, initial_agent_info, N, monster_coords, sensor_range=4, fuel=100, health=100, location=(0,0)):
        self.available_actions = ['up', 'down', 'right', 'left', 'scan', 'collect', 'dock']
        self.health = health
        self.sensor_range = sensor_range
        self.fuel = fuel
        self.location = location
        self.N = N
        self.monster_coords = set(monster_coords)
        self.memory = {}
        self.resources = {"water": 0, "minerals": 0, "oxygen": 0}
        self.mapped_percentage = 0.0
        self.resource_goals = initial_agent_info.get('resource_goals', {"water":10, "minerals":15, "oxygen":5})
        self.planets_in_memory = []
        
        # Navigation tracking
        self.visited_locations = set([location])
        self.last_positions = deque([location], maxlen=10)
        self.current_target = None
        self.fuel_reserve = 40  # Increased fuel reserve
        self.conservative_mode = False

    def in_loop(self):
        """Check if agent is stuck in a movement loop"""
        if len(self.last_positions) < self.last_positions.maxlen:
            return False
        # If we have more than half duplicates in recent positions, we're likely in a loop
        return len(set(self.last_positions)) < len(self.last_positions)/2

    def get_next_move(self, environment):
        """Smart move selection prioritizing fuel stations"""
        # Emergency fuel situation
        if self.fuel <= self.fuel_reserve:
            station = self.find_nearest_reachable_station(environment)
            if station:
                path = self.find_fuel_efficient_path(self.location, station, environment)
                if path:
                    next_pos = path[0]
                    return self.get_move_action(self.location, next_pos)
                else:
                    # Try to find any reachable station
                    for station in environment.space_stations:
                        path = self.find_fuel_efficient_path(self.location, station['position'], environment)
                        if path and len(path) <= self.fuel:
                            next_pos = path[0]
                            return self.get_move_action(self.location, next_pos)
        
        # If no target or stuck, choose new target
        if not self.current_target or self.in_loop():
            self.select_new_target(environment)
        
        # Get path to current target with fuel check
        if self.current_target:
            path = self.find_fuel_efficient_path(self.location, self.current_target, environment)
            if path and len(path) <= (self.fuel - self.fuel_reserve):
                next_pos = path[0]
                return self.get_move_action(self.location, next_pos)
            else:
                # Target is too far - find fuel first
                station = self.find_nearest_reachable_station(environment)
                if station:
                    self.current_target = station
                    path = self.find_fuel_efficient_path(self.location, station, environment)
                    if path:
                        next_pos = path[0]
                        return self.get_move_action(self.location, next_pos)
        
        # Fallback to safe exploration
        return self.explore_safely(environment)

    def find_fuel_efficient_path(self, start, goal, environment):
        """A* pathfinding that prioritizes safe, fuel-efficient routes"""
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}
        
        while frontier:
            current = heapq.heappop(frontier)[1]
            
            if current == goal:
                break
            
            for next_pos in self.get_safe_neighbors(current, environment):
                # Cost adjustments:
                move_cost = 1  # Base cost
                if environment.grid[next_pos] == 5:  # Nebula
                    move_cost = 2
                elif environment.grid[next_pos] in [3,6] or next_pos in self.monster_coords:
                    move_cost = 5
                
                new_cost = cost_so_far[current] + move_cost
                
                if (next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]) and new_cost <= self.fuel:
                    cost_so_far[next_pos] = new_cost
                    priority = new_cost + heuristic(goal, next_pos)
                    heapq.heappush(frontier, (priority, next_pos))
                    came_from[next_pos] = current
        
        # Reconstruct path
        path = []
        current = goal
        while current != start:
            path.append(current)
            current = came_from.get(current)
            if current is None or current in path:
                return []
        
        path.reverse()
        return path

    def get_safe_neighbors(self, position, environment):
        """Get neighboring positions with safety weights"""
        row, col = position
        neighbors = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            r, c = row + dr, col + dc
            if 0 <= r < self.N and 0 <= c < self.N:
                weight = 0
                if (r,c) in self.last_positions:
                    weight += 3
                if (r,c) not in self.memory:
                    weight -= 2
                if environment.grid[r,c] in [3,6] or (r,c) in self.monster_coords:
                    weight += 5
                neighbors.append((weight, (r,c)))
        
        return [pos for _, pos in sorted(neighbors, key=lambda x: x[0])]

    def find_nearest_reachable_station(self, environment):
        """Find nearest reachable space station"""
        nearest = None
        min_dist = float('inf')
        for station in environment.space_stations:
            dist = self.heuristic(self.location, station['position'])
            if dist < min_dist:
                path = self.find_fuel_efficient_path(self.location, station['position'], environment)
                if path and len(path) <= self.fuel:
                    nearest = station['position']
                    min_dist = dist
        return nearest

    def select_new_target(self, environment):
        """Choose targets based on mission priorities with fuel awareness"""
        options = []
        needed = self.calculate_needed_resources()
        
        # 1. Always prioritize stations when fuel is below 60
        if self.fuel < 60:
            station = self.find_nearest_reachable_station(environment)
            if station:
                dist = self.heuristic(self.location, station)
                priority = (100 - self.fuel)/max(1, dist)
                options.append((priority, station))
        
        # 2. Resource collection (only if we have good fuel)
        if self.fuel > self.fuel_reserve + 20:
            for planet in self.planets_in_memory:
                if planet['resource_amount'] > 0 and needed.get(planet['resource_type'], 0) > 0:
                    dist = self.heuristic(self.location, planet['position'])
                    resource_priority = needed[planet['resource_type']] / self.resource_goals[planet['resource_type']]
                    priority = (resource_priority * 2.0) / max(1, dist)
                    options.append((priority, planet['position']))
        
        # 3. Exploration (only with ample fuel)
        if self.fuel > 70:
            unexplored = self.find_unexplored_frontier()
            if unexplored:
                options.append((0.5, unexplored))
        
        # 4. Endpoint if mission complete
        if all(v <= 0 for v in needed.values()):
            dist = self.heuristic(self.location, environment.end_position)
            options.append((3.0/max(1, dist), environment.end_position))
        
        # Select highest priority reachable target
        if options:
            for priority, target in sorted(options, reverse=True):
                path = self.find_fuel_efficient_path(self.location, target, environment)
                if path and len(path) <= (self.fuel - self.fuel_reserve):
                    self.current_target = target
                    return
        
        # Fallback: find any safe spot
        self.current_target = self.find_random_safe_spot(environment)

    def find_unexplored_frontier(self):
        """Find boundary between explored and unexplored areas"""
        frontier = []
        for (r,c), val in self.memory.items():
            if val != 7:  # Not unexplored
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if (0 <= nr < self.N and 0 <= nc < self.N and 
                        (nr,nc) not in self.memory):
                        frontier.append((nr,nc))
        return random.choice(frontier) if frontier else None

    def find_random_safe_spot(self, environment):
        """Find a random accessible position that's safe"""
        safe_spots = []
        for r in range(self.N):
            for c in range(self.N):
                pos = (r, c)
                if (environment.grid[pos] not in [3,6] and
                    pos not in self.monster_coords and
                    pos != self.location):
                    safe_spots.append(pos)
        return random.choice(safe_spots) if safe_spots else None

    def explore_safely(self, environment):
        """Fallback exploration with loop prevention"""
        safe_moves = []
        for action in ['up','down','left','right']:
            new_pos = self.get_new_position(self.location, action)
            if (0 <= new_pos[0] < self.N and 
                0 <= new_pos[1] < self.N and 
                new_pos not in self.last_positions and
                environment.grid[new_pos] not in [3,6] and
                new_pos not in self.monster_coords):
                safe_moves.append(action)
        
        return random.choice(safe_moves) if safe_moves else None

    def get_new_position(self, position, action):
        """Calculate new position after action"""
        row, col = position
        if action == 'up':
            return (row - 1, col)
        elif action == 'down':
            return (row + 1, col)
        elif action == 'left':
            return (row, col - 1)
        elif action == 'right':
            return (row, col + 1)
        return position

    def choose_action(self, environment):
        """Main decision-making function with mission focus"""
        self.last_positions.append(self.location)
        self.visited_locations.add(self.location)
        
        # Emergency fuel situation
        if self.fuel <= self.fuel_reserve:
            station = self.find_nearest_reachable_station(environment)
            if station:
                path = self.find_fuel_efficient_path(self.location, station, environment)
                if path:
                    next_pos = path[0]
                    return self.get_move_action(self.location, next_pos)
        
        # Special actions
        if environment.grid[self.location] == 4 and self.fuel < 90:
            return 'dock'
        if (environment.grid[self.location] == 2 and 
            any(p['position'] == self.location and p['resource_amount'] > 0 
                for p in self.planets_in_memory)):
            return 'collect'
        
        # Normal movement
        action = self.get_next_move(environment)
        if action:
            return action
        
        # Final fallback
        if 'scan' in self.actions(self.location) and self.fuel > self.fuel_reserve + 10:
            return 'scan'
        return None

    def calculate_needed_resources(self):
        """Calculate which resources still need to be collected"""
        return {
            res: max(0, amount - self.resources.get(res, 0))
            for res, amount in self.resource_goals.items()
        }

    def heuristic(self, a, b):
        """Manhattan distance heuristic"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def get_move_action(self, current, next_pos):
        """Determine movement action between positions"""
        dr = next_pos[0] - current[0]
        dc = next_pos[1] - current[1]
        if dr == -1: return 'up'
        if dr == 1: return 'down'
        if dc == -1: return 'left'
        if dc == 1: return 'right'
        return None

    def actions(self, location):
        """Get available actions at current location"""
        if self.health <= 0 or self.fuel <= 0:
            return []
            
        possible_actions = self.available_actions[:]
        row, col = location

        # Boundary checks
        if row == 0: possible_actions.remove('up')
        if row == self.N - 1: possible_actions.remove('down')
        if col == 0: possible_actions.remove('left')
        if col == self.N - 1: possible_actions.remove('right')

        return possible_actions

    def move(self, action, environment):
        """Execute movement with collision detection"""
        if action not in self.actions(self.location):
            return False
            
        new_location = self.get_new_position(self.location, action)
        
        # Check for collisions
        if new_location in [m['position'] for m in environment.meteors]:
            self.health -= 10
        elif environment.grid[new_location] == 6:  # Radiation
            self.health -= 5
        
        # Update position
        self.location = new_location
        self.fuel -= 1
        self.visited_locations.add(new_location)
        self.last_positions.append(new_location)
        
        # Update environment grid
        environment.grid[self.location] = 1  # AGENT
        
        return True

    def collect_resources(self, environment):
        """Collect resources from current planet"""
        if environment.grid[self.location] != 2:  # Not on planet
            return False
            
        for planet in environment.planets:
            if planet['position'] == self.location:
                resource_type = planet['resource_type']
                amount = min(planet['resource_amount'], 5)
                self.resources[resource_type] += amount
                planet['resource_amount'] -= amount
                
                if planet['resource_amount'] <= 0:
                    environment.grid[self.location] = 0
                return True
        return False

    def dock(self, environment):
        """Refuel at space station"""
        if environment.grid[self.location] != 4:  # Not at station
            return False
            
        self.fuel = min(100, self.fuel + 70)
        return True

    def scan_area(self, environment):
        """Perform area scan"""
        self.sense(self.location, environment)
        return True

    def sense(self, location, environment):
        """Update agent's knowledge of environment"""
        sensed_cells = set()
        row, col = location
        
        # Adjust sensor range in nebulas
        current_range = self.sensor_range
        if environment.grid[location] == 5:  # In nebula
            current_range = max(1, current_range - 2)
        
        # Scan area
        for r in range(max(0, row-current_range), min(self.N, row+current_range+1)):
            for c in range(max(0, col-current_range), min(self.N, col+current_range+1)):
                sensed_cells.add((r, c))
                self.memory[(r, c)] = environment.grid[r, c]
                
                # Track planets
                if environment.grid[r, c] == 2:  # PLANET
                    planet_info = next((p for p in environment.planets if p['position'] == (r, c)), None)
                    if planet_info and planet_info not in self.planets_in_memory:
                        self.planets_in_memory.append(planet_info)
        
        # Update mapped percentage
        total_cells = self.N * self.N
        self.mapped_percentage = (len(self.memory) / total_cells) * 100
        return sensed_cells