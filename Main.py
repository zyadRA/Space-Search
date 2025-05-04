import random
from SpaceEnvironment import SpaceEnvironment
import time

# initialize env and agent state
env = SpaceEnvironment(grid=(20,20))
env.intialize_env()

agent_state = {
    "position": env.starting_position,
        "fuel": 100,
        "health": 100,
        "collected_resources": {"water": 0, "minerals": 0, "oxygen": 0},
        "explored_cells": {env.starting_position},
        "covered_map_percentage": 0.0
}

game_over = False
total_decision_time =0
# game loop
print("------------------start game-----------------------------------")
print(f"starting position: {env.starting_position}")
while not game_over and env.timestep <200:
    print(f"Timestep {env.timestep}:")
    
    print("agent state")
    print(agent_state)
    # get allowed actoins
    allowed_actions = env.actions(agent_state)
    print(f"ALLOWED ACTIONS: {allowed_actions}")

    # agent goes here
    # random action for now
    # if "DOCK" in allowed_actions:
    #     action = "DOCK"
    # elif "COLLECT" in allowed_actions:
    #     action = "COLLECT"
    start_time = time.time()
    action = random.choice(allowed_actions)
    end_time = time.time()

    total_decision_time += (end_time-start_time)
    
    print(f"CHOSEN ACTION IS: {action}")

    # result
    result = env.do_action(agent_state, action)
    agent_state = result["agent_state"]
    percepts = result["percepts"]

    env.update_env(agent_state)
    
    print(f"agent state after doing {action}: ")
    print(agent_state)
    print(f"PERCEPTS: {percepts}")
    

    game_status = env.is_game_over(agent_state) 
    print(f"game status: {game_status}")
    print("--------------------------------------------------------")
    game_over = game_status["is_game_over"]

# EVALUATION

# timesteps
total_timesteps = env.timestep

# agent decision time
avg_decision_time = total_decision_time / (total_timesteps+1)

print(f"TOTAL TIMESTEPS: {total_timesteps}")
print(f"TOTAL DECISION TIME: {total_decision_time}")
print(f"AVERAGE DECISION TIME BY AGENT: {avg_decision_time}")

# if agent achieved goal and how close he is from goal
map_coverage = f"MAP COVERAGE GOAL:{env.mapping_goal_percentage} ACHIEVED: {agent_state['covered_map_percentage']}" if game_status['is_map_covered'] else f"MAP COVERAGE GOAL:{env.mapping_goal_percentage} WASN'T ACHIEVED: {agent_state['covered_map_percentage']}"
resources_met = f"RESOURCES GOAL:{env.resource_goals} ACHIEVED: {agent_state['collected_resources']}" if game_status['is_resources_met'] else f"RESOURCES GOAL:{env.resource_goals} WASN'T ACHIEVED: {agent_state['collected_resources']}"
print(map_coverage)
print(resources_met)