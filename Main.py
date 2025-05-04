import random
from SpaceEnvironment import SpaceEnvironment

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
    action = random.choice(allowed_actions)
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
