import random
from SpaceEnvironment import SpaceEnvironment
import time
from Spacecraft import Agent  # Correctly import Agent from Spacecraft file

# Initialize environment
env = SpaceEnvironment(grid=(20, 20))
env.initialize_env()

# Initialize agent state
agent_state = {
    "position": env.starting_position,
    "fuel": 100,
    "health": 100,
    "collected_resources": {"water": 0, "minerals": 0, "oxygen": 0},
    "explored_cells": {env.starting_position},
    "covered_map_percentage": 0.0
}

# Create initial_agent_info dictionary from the environment
initial_agent_info = {
    'resource_goals': env.resource_goals
}

# Collect dangerous entity positions (meteors and radiation zones) for monster_coords
monster_coords = set()
for meteor in env.meteors:
    monster_coords.add(meteor["position"])
for radiation in env.radiation_zones:
    monster_coords.add(radiation["position"])

# Initialize agent with environment grid size and dangerous entities
agent = Agent(initial_agent_info, env.grid_size[0], monster_coords=monster_coords, location=env.starting_position)

# Do an initial scan to build the agent's knowledge
result = env.do_action(agent_state, "SCAN")
agent_state = result["agent_state"]
percepts = result["percepts"]
agent.sense(agent_state["position"], env)  # Update agent memory with percepts

# Sync agent properties with agent_state
agent.location = agent_state["position"]
agent.fuel = agent_state["fuel"]
agent.health = agent_state["health"]
agent.resources = agent_state["collected_resources"].copy()

game_over = False
total_decision_time = 0
timesteps_without_progress = 0
max_timesteps = 200

# Game loop
print("------------------start game-----------------------------------")
print(f"Starting position: {env.starting_position}")
print(f"End position: {env.end_position}")
print(f"Resource goals: {env.resource_goals}")
print(f"Mapping goal: {env.mapping_goal_percentage}%")

while not game_over :
    print(f"Timestep {env.timestep}:")
    
    # Print current state
    print(f"Position: {agent_state['position']}")
    print(f"Current target: {agent.current_target}")
    print(f"Last decision: {agent.last_decision_reason}")
    print(f"Fuel: {agent_state['fuel']}, Health: {agent_state['health']}")
    print(f"Collected: {agent_state['collected_resources']}")
    print(f"Map coverage: {agent_state['covered_map_percentage']:.2f}%")
    
    # Get allowed actions
    allowed_actions = env.actions(agent_state)
    print(f"Allowed actions: {allowed_actions}")

    # Update agent properties from agent_state
    agent.location = agent_state["position"]
    agent.fuel = agent_state["fuel"]
    agent.health = agent_state["health"]
    agent.resources = agent_state["collected_resources"].copy()
    
    # Use the agent to decide the action
    start_time = time.time()
    action = agent.choose_action(env, allowed_actions)
    end_time = time.time()

    total_decision_time += (end_time-start_time)
    
    print(f"CHOSEN ACTION IS: {action}")

    # Store previous state to detect progress
    prev_position = agent_state["position"]
    prev_resources = {k: v for k, v in agent_state["collected_resources"].items()}
    prev_coverage = agent_state["covered_map_percentage"]

    # Execute action
    result = env.do_action(agent_state, action)
    agent_state = result["agent_state"]
    percepts = result["percepts"]
    
    # Check if we made progress
    made_progress = False
    if prev_position != agent_state["position"]:
        made_progress = True  # Moved
    for k, v in agent_state["collected_resources"].items():
        if v > prev_resources.get(k, 0):
            made_progress = True  # Collected resources
    if agent_state["covered_map_percentage"] > prev_coverage + 0.5:
        made_progress = True  # Discovered new areas
        
    if made_progress:
        timesteps_without_progress = 0
    else:
        timesteps_without_progress += 1
        
    # Emergency break if stuck too long
    if timesteps_without_progress > 20:
        print("WARNING: Agent seems to be stuck, forcing random action...")
        # Force a random action to break out of loops
        if len(allowed_actions) > 1:  # More than just SCAN
            action = random.choice([a for a in allowed_actions if a != "SCAN"])
            result = env.do_action(agent_state, action)
            agent_state = result["agent_state"]
            percepts = result["percepts"]
        timesteps_without_progress = 0
    
    # Update agent's memory if we got percepts
    if percepts:
        agent.sense(agent_state["position"], env)
        
    # Update monster_coords with current meteor and radiation zone positions
    agent.monster_coords = set()
    for meteor in env.meteors:
        agent.monster_coords.add(meteor["position"])
    for radiation in env.radiation_zones:
        agent.monster_coords.add(radiation["position"])

    # Update environment
    env.update_env(agent_state)
    
    print(f"After action: Position={agent_state['position']}, Fuel={agent_state['fuel']}, Health={agent_state['health']}")
    print(f"Percepts: {len(percepts) if percepts else 0} items seen")
    
    # Check game status
    game_status = env.is_game_over(agent_state)
    print(f"Game status: {game_status}")
    print("--------------------------------------------------------")
    game_over = game_status["is_game_over"]

# EVALUATION
total_timesteps = env.timestep
avg_decision_time = total_decision_time / (total_timesteps+1)

print("\n=================== FINAL RESULTS ===================")
print(f"TOTAL TIMESTEPS: {total_timesteps}")
