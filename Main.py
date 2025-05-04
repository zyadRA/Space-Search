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

# game loop
