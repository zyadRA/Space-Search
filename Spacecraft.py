import heapq
import random
import math
from collections import deque

class Agent:
    def __init__(self, initial_agent_info, N, monster_coords=None, sensor_range=3, fuel=100, health=100, location=(0,0)):
        self.available_actions = ['UP', 'DOWN', 'RIGHT', 'LEFT', 'SCAN', 'COLLECT', 'DOCK']
        self.health = health
        self.sensor_range = sensor_range
        self.fuel = fuel
        self.location = location
        self.N = N
        self.monster_coords = monster_coords if monster_coords else set()
        self.memory = {}
        self.resources = {"water": 0, "minerals": 0, "oxygen": 0}
        self.mapped_percentage = 0.0
        self.resource_goals = initial_agent_info.get('resource_goals', {"water":10, "minerals":15, "oxygen":5})
        self.planets_in_memory = []
        self.visited_locations = set([location])
        self.last_positions = deque([location], maxlen=10)
        self.current_target = None
        self.fuel_reserve = 20
        self.last_scan_position = None
        self.resource_priority_multiplier = 4.0
        self.exploration_priority_multiplier = 3.0
        self.target_history = []
        self.last_decision_reason = ""

    def in_loop(self):
        if len(self.last_positions) < self.last_positions.maxlen:
            return False
        return len(set(self.last_positions)) < len(self.last_positions)/2

    def get_next_move(self, environment):
        if self.fuel < 15:
            self.last_decision_reason = "Emergency fuel - critically low"
            station = self.find_nearest_reachable_station(environment)
            if station:
                path = self.find_safe_path(self.location, station, environment)
                if path:
                    next_pos = path[0]
                    return self.get_move_action(self.location, next_pos)
        
        if not self.current_target or self.in_loop():
            self.select_new_target(environment)
        
        if self.current_target:
            path = self.find_safe_path(self.location, self.current_target, environment)
            if path and len(path) <= (self.fuel - 10):
                next_pos = path[0]
                return self.get_move_action(self.location, next_pos)
            else:
                self.last_decision_reason = "Target too far, reassessing"
                self.select_new_target(environment)
                if self.current_target:
                    path = self.find_safe_path(self.location, self.current_target, environment)
                    if path:
                        next_pos = path[0]
                        return self.get_move_action(self.location, next_pos)
        
        self.last_decision_reason = "Active exploration"
        return self.explore_actively(environment)

    def find_safe_path(self, start, goal, environment):
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}
        
        while frontier:
            _, current = heapq.heappop(frontier)
            
            if current == goal:
                break
            
            for next_pos in self.get_safe_neighbors(current, environment):
                move_cost = 1
                
                if next_pos in self.memory:
                    cell_type = self.memory[next_pos]
                    if cell_type == 5:
                        move_cost = 2
                    elif cell_type in [3, 6] or next_pos in self.monster_coords:
                        move_cost = 20
                
                new_cost = cost_so_far[current] + move_cost
                
                if (next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]) and new_cost <= self.fuel:
                    cost_so_far[next_pos] = new_cost
                    priority = new_cost + heuristic(next_pos, goal)
                    heapq.heappush(frontier, (priority, next_pos))
                    came_from[next_pos] = current
        
        if goal not in came_from:
            return []
            
        path = []
        current = goal
        while current != start:
            path.append(current)
            current = came_from[current]
            if current is None or current in path:
                return []
        
        path.reverse()
        return path

    def get_safe_neighbors(self, position, environment):
        row, col = position
        neighbors = []
        
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            r, c = row + dr, col + dc
            if 0 <= r < self.N and 0 <= c < self.N:
                weight = 0
                pos = (r, c)
                
                if pos in self.last_positions:
                    weight += 5
                
                if pos not in self.memory:
                    weight -= 4
                
                if pos in self.memory and self.memory[pos] in [3, 6]:
                    weight += 50
                if pos in self.monster_coords:
                    weight += 50
                
                neighbors.append((weight, pos))
        
        neighbors.sort(key=lambda x: x[0])
        return [pos for _, pos in neighbors]

    def find_nearest_reachable_station(self, environment):
        nearest = None
        min_dist = float('inf')
        
        for station in environment.space_stations:
            dist = self.heuristic(self.location, station['position'])
            if dist < min_dist:
                path = self.find_safe_path(self.location, station['position'], environment)
                if path and len(path) <= self.fuel:
                    nearest = station['position']
                    min_dist = dist
        
        return nearest

    def select_new_target(self, environment):
        options = []
        needed_resources = self.calculate_needed_resources()
        old_target = self.current_target
        
        if any(needed_resources.values()):
            for planet in self.planets_in_memory:
                if planet.get('resource_amount', 0) > 0:
                    resource_type = planet.get('resource_type')
                    if needed_resources.get(resource_type, 0) > 0:
                        dist = self.heuristic(self.location, planet['position'])
                        
                        resource_priority = needed_resources[resource_type] / max(1, self.resource_goals[resource_type])
                        
                        priority = (resource_priority * self.resource_priority_multiplier) / max(1, dist)
                        
                        fuel_needed = dist + 5
                        if self.fuel >= fuel_needed:
                            options.append((priority, planet['position'], f"Need {resource_type}"))
        
        if self.mapped_percentage < environment.mapping_goal_percentage:
            exploration_targets = self.find_exploration_targets()
            
            for dist, target in exploration_targets[:5]:
                exploration_priority = 1.0 - (self.mapped_percentage / environment.mapping_goal_percentage)
                priority = (exploration_priority * self.exploration_priority_multiplier) / max(1, dist)
                
                fuel_needed = dist + 5
                if self.fuel >= fuel_needed:
                    options.append((priority, target, "Exploration"))
        
        if self.fuel < 30:
            station = self.find_nearest_reachable_station(environment)
            if station:
                dist = self.heuristic(self.location, station)
                priority = (30 - self.fuel)/max(1, dist * 2)
                options.append((priority, station, "Getting low on fuel"))
        
        resources_met = all(v <= 0 for v in needed_resources.values())
        map_covered = self.mapped_percentage >= environment.mapping_goal_percentage
        
        if resources_met and map_covered and environment.end_position:
            dist = self.heuristic(self.location, environment.end_position)
            if self.fuel >= dist:
                options.append((10.0, environment.end_position, "Mission complete, going to end"))
        
        if options:
            options.sort(reverse=True)
            
            for priority, target, reason in options:
                path = self.find_safe_path(self.location, target, environment)
                if path and len(path) <= (self.fuel - 5):
                    self.current_target = target
                    self.last_decision_reason = reason
                    self.target_history.append((target, reason))
                    
                    if old_target != target:
                        self.last_positions = deque([self.location], maxlen=10)
                    return
        
        fallback_target = self.find_exploration_spot(environment)
        if fallback_target:
            self.current_target = fallback_target
            self.last_decision_reason = "Exploration fallback"
            self.target_history.append((fallback_target, "Fallback exploration"))

    def find_exploration_targets(self):
        frontier = []
        
        for (r, c) in self.memory:
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r + dr, c + dc
                pos = (nr, nc)
                
                if (0 <= nr < self.N and 0 <= nc < self.N and pos not in self.memory):
                    unexplored_neighbors = 0
                    for dr2, dc2 in [(-1,0), (1,0), (0,-1), (0,1)]:
                        r2, c2 = nr + dr2, nc + dc2
                        if (0 <= r2 < self.N and 0 <= c2 < self.N and (r2, c2) not in self.memory):
                            unexplored_neighbors += 1
                    
                    dist = self.heuristic(self.location, pos)
                    
                    score = unexplored_neighbors
                    
                    if self.last_scan_position and self.heuristic(pos, self.last_scan_position) < 4:
                        score -= 2
                    
                    frontier.append((dist, pos, score))
        
        frontier.sort(key=lambda x: (-x[2], x[0]))
        
        return [(dist, pos) for dist, pos, _ in frontier]

    def find_exploration_spot(self, environment):
        targets = self.find_exploration_targets()
        if targets:
            for dist, target in targets:
                if dist <= self.fuel - 5:
                    path = self.find_safe_path(self.location, target, environment)
                    if path:
                        return target
        
        potential_spots = []
        
        for pos in self.memory:
            if self.memory[pos] not in [3, 6] and pos not in self.monster_coords:
                has_unexplored = False
                for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nr, nc = pos[0] + dr, pos[1] + dc
                    if (0 <= nr < self.N and 0 <= nc < self.N and (nr, nc) not in self.memory):
                        has_unexplored = True
                        break
                
                if has_unexplored:
                    dist = self.heuristic(self.location, pos)
                    if dist <= self.fuel - 5:
                        potential_spots.append((dist, pos))
        
        potential_spots.sort()
        return potential_spots[0][1] if potential_spots else None

    def explore_actively(self, environment):
        safe_moves = []
        
        for action in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
            new_pos = self.get_new_position(self.location, action)
            
            if (0 <= new_pos[0] < self.N and 0 <= new_pos[1] < self.N):
                is_safe = True
                if new_pos in self.memory:
                    if self.memory[new_pos] in [3, 6]:
                        is_safe = False
                if new_pos in self.monster_coords:
                    is_safe = False
                    
                if is_safe:
                    unexplored_value = 0
                    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                        nr, nc = new_pos[0] + dr, new_pos[1] + dc
                        if (0 <= nr < self.N and 0 <= nc < self.N and (nr, nc) not in self.memory):
                            unexplored_value += 2
                    
                    if new_pos not in self.memory:
                        unexplored_value += 5
                    
                    revisit_penalty = 2 if new_pos in self.last_positions else 0
                    
                    score = unexplored_value - revisit_penalty
                    safe_moves.append((score, action))
        
        if safe_moves:
            safe_moves.sort(reverse=True)
            return safe_moves[0][1]
        
        return 'SCAN'

    def get_new_position(self, position, action):
        row, col = position
        if action == 'UP':
            return (row - 1, col)
        elif action == 'DOWN':
            return (row + 1, col)
        elif action == 'LEFT':
            return (row, col - 1)
        elif action == 'RIGHT':
            return (row, col + 1)
        return position

    def choose_action(self, environment, allowed_actions):
        self.last_positions.append(self.location)
        self.visited_locations.add(self.location)
        
        if 'COLLECT' in allowed_actions:
            for planet in environment.planets:
                if planet['position'] == self.location and planet['resource_amount'] > 0:
                    self.last_decision_reason = f"Collecting {planet['resource_type']}"
                    return 'COLLECT'
        
        should_scan = False
        
        if len(self.memory) < 20:
            should_scan = True
        
        elif self.last_scan_position and self.heuristic(self.location, self.last_scan_position) > 3:
            should_scan = True
        
        else:
            unexplored_count = 0
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = self.location[0] + dr, self.location[1] + dc
                if (0 <= nr < self.N and 0 <= nc < self.N and (nr, nc) not in self.memory):
                    unexplored_count += 1
            
            if unexplored_count > 0:
                should_scan = True
        
        if should_scan and 'SCAN' in allowed_actions and self.fuel > 10:
            self.last_decision_reason = "Scanning to map environment"
            self.last_scan_position = self.location
            return 'SCAN'
        
        if 'DOCK' in allowed_actions and self.fuel < 90:
            self.last_decision_reason = "Refueling at station"
            return 'DOCK'
        
        move_action = self.get_next_move(environment)
        if move_action in allowed_actions:
            return move_action
        
        if 'SCAN' in allowed_actions:
            self.last_decision_reason = "Fallback scan"
            self.last_scan_position = self.location
            return 'SCAN'
        
        move_actions = [a for a in allowed_actions if a in ['UP', 'DOWN', 'LEFT', 'RIGHT']]
        if move_actions:
            return random.choice(move_actions)
            
        self.last_decision_reason = "No viable actions"
        return allowed_actions[0]

    def calculate_needed_resources(self):
        return {
            res: max(0, amount - self.resources.get(res, 0))
            for res, amount in self.resource_goals.items()
        }

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def get_move_action(self, current, next_pos):
        dr = next_pos[0] - current[0]
        dc = next_pos[1] - current[1]
        
        if dr == -1 and dc == 0: return 'UP'
        if dr == 1 and dc == 0: return 'DOWN'
        if dr == 0 and dc == -1: return 'LEFT'
        if dr == 0 and dc == 1: return 'RIGHT'
        
        return None

    def actions(self, location):
        if self.health <= 0 or self.fuel <= 0:
            return []
            
        possible_actions = self.available_actions[:]
        row, col = location

        if row == 0: possible_actions.remove('UP')
        if row == self.N - 1: possible_actions.remove('DOWN')
        if col == 0: possible_actions.remove('LEFT')
        if col == self.N - 1: possible_actions.remove('RIGHT')

        return possible_actions

    def sense(self, location, environment):
        sensed_cells = set()
        row, col = location
        
        current_range = self.sensor_range
        if environment.grid[location] == 5:
            current_range = max(1, current_range - 1)
        
        for r in range(max(0, row-current_range), min(self.N, row+current_range+1)):
            for c in range(max(0, col-current_range), min(self.N, col+current_range+1)):
                pos = (r, c)
                sensed_cells.add(pos)
                
                self.memory[pos] = environment.grid[pos]
                
                if environment.grid[pos] == 2:
                    planet_info = next((p for p in environment.planets if p['position'] == pos), None)
                    if planet_info:
                        existing_planet = next((p for p in self.planets_in_memory if p['position'] == pos), None)
                        if existing_planet:
                            existing_planet['resource_amount'] = planet_info['resource_amount']
                            existing_planet['resource_type'] = planet_info['resource_type']
                        else:
                            self.planets_in_memory.append(planet_info.copy())
                            
        total_cells = self.N * self.N
        self.mapped_percentage = (len(self.memory) / total_cells) * 100
        
        return sensed_cells