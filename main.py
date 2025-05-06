import random
from SpaceEnvironment import SpaceEnvironment
import time
from Spacecraft import Agent  

env = SpaceEnvironment(grid=(20, 20))
env.initialize_env()

# initial agent state
agent_state = {
    "position": env.starting_position,
    "fuel": 100,
    "health": 100,
    "collected_resources": {"water": 0, "minerals": 0, "oxygen": 0},
    "explored_cells": {env.starting_position},
    "covered_map_percentage": 0.0
}

initial_agent_info = {
    'resource_goals': env.resource_goals
}


# create agent
agent = Agent(initial_agent_info, env.grid_size[0], location=env.starting_position)

# initial scan
result = env.do_action(agent_state, "SCAN")
agent_state = result["agent_state"]
percepts = result["percepts"]
# update agent with percepts
agent.sense(agent_state["position"], env)

agent.location = agent_state["position"]
agent.fuel = agent_state["fuel"]
agent.health = agent_state["health"]
agent.resources = agent_state["collected_resources"].copy()

game_over = False
total_decision_time = 0
timesteps_without_progress = 0
max_timesteps = 200

# GAME LOOP
print("------------------start game-----------------------------------")
print(f"Starting position: {env.starting_position}")
print(f"End position: {env.end_position}")
print(f"Resource goals: {env.resource_goals}")
print(f"Mapping goal: {env.mapping_goal_percentage}%")

while not game_over :
    print(f"Timestep {env.timestep}:")
    
    # current state
    print(f"Position: {agent_state['position']}")
    print(f"Current target: {agent.current_target}")
    print(f"Last decision: {agent.last_decision_reason}")
    print(f"Fuel: {agent_state['fuel']}, Health: {agent_state['health']}")
    print(f"Collected: {agent_state['collected_resources']}")
    print(f"Map coverage: {agent_state['covered_map_percentage']:.2f}%")
    
    allowed_actions = env.actions(agent_state)
    print(f"Allowed actions: {allowed_actions}")

    # update agent
    agent.location = agent_state["position"]
    agent.fuel = agent_state["fuel"]
    agent.health = agent_state["health"]
    agent.resources = agent_state["collected_resources"].copy()
    
    # DICISION
    start_time = time.time()
    action = agent.choose_action(env, allowed_actions)
    end_time = time.time()

    total_decision_time += (end_time-start_time)
    
    print(f"CHOSEN ACTION IS: {action}")

    
    # do action
    result = env.do_action(agent_state, action)
    agent_state = result["agent_state"]
    percepts = result["percepts"]
    
    # add percepts
    if percepts:
        agent.sense(agent_state["position"], env)
        
    # update danger positions
    agent.monster_coords = set()
    for meteor in env.meteors:
        agent.monster_coords.add(meteor["position"])
    for radiation in env.radiation_zones:
        agent.monster_coords.add(radiation["position"])

    env.update_env(agent_state)
    
    print(f"After action: Position={agent_state['position']}, Fuel={agent_state['fuel']}, Health={agent_state['health']}")
    print(f"Percepts: {len(percepts) if percepts else 0} items seen")
    
    # game status
    game_status = env.is_game_over(agent_state)
    print(f"Game status: {game_status}")
    print("--------------------------------------------------------")
    game_over = game_status["is_game_over"]

# EVALUATION
total_timesteps = env.timestep
avg_decision_time = total_decision_time / (total_timesteps+1)

print("\n=================== FINAL RESULTS ===================")
print(f"TOTAL TIMESTEPS: {total_timesteps}")
print(f"AVERAGE DECISION TIME: {avg_decision_time}")
