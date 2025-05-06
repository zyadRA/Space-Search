from ENV import (
    SpaceEnvironment,
    EMPTY,
    AGENT,
    PLANET,
    METEOR,
    SPACE_STATION,
    NEBULA,
    RADIATION_ZONE,
    UNEXPLORED,
    END
)
from Agent import Agent
import random

from ENV import SpaceEnvironment
from Agent import Agent
import random

def main():
    # Initialize the environment
    env = SpaceEnvironment((20, 20))
    
    # Set up the environment with entities (now calling the correctly spelled method)
    env.initialize_env(
        num_planets=5,
        num_meteors=8,
        num_space_stations=3,
        num_nebulas=4,
        num_radiation_zones=3,
        mapping_goal_percentage=70.0,
        resource_goals={"water": 10, "minerals": 15, "oxygen": 5}
    )
    
    # Rest of the code remains the same...
    # Initialize the agent with proper state structure
    agent_state = {
        "position": env.starting_position,
        "fuel": 100,
        "health": 100,
        "collected_resources": {"water": 0, "minerals": 0, "oxygen": 0},
        "covered_map_percentage": 0.0,
        "explored_cells": set()
    }
    
    agent = Agent(
        initial_agent_info={
            "resource_goals": env.resource_goals,
            "position": env.starting_position,
            "fuel": 100,
            "health": 100
        },
        N=20,
        monster_coords=[m['position'] for m in env.meteors],
        sensor_range=4
    )
    
    # Main game loop
    max_steps = 200
    current_step = 0
    
    print("Starting space exploration mission!")
    print(f"Mission goals: Collect resources {env.resource_goals}, map {env.mapping_goal_percentage}% of space")
    print(f"Starting position: {env.starting_position}, End position: {env.end_position}")
    
    while current_step < max_steps:
        print(f"\n=== Step {current_step + 1} ===")
        print(f"Agent status - Health: {agent.health}, Fuel: {agent.fuel}, Resources: {agent.resources}")
        print(f"Mapped: {agent.mapped_percentage:.1f}% of space")
        print(f"Current position: {agent.location}")
        
        # Update agent state
        agent_state = {
            "position": agent.location,
            "fuel": agent.fuel,
            "health": agent.health,
            "collected_resources": agent.resources,
            "covered_map_percentage": agent.mapped_percentage,
            "explored_cells": set(agent.memory.keys())
        }
        
        # Check game state
        game_state = env.is_game_over(agent_state)
        
        if game_state["is_game_over"]:
            if agent.location == env.end_position:
                print("\nMission accomplished! Reached endpoint!")
            elif agent.health <= 0:
                print("\nAgent destroyed! Mission failed.")
            elif agent.fuel <= 0:
                print("\nOut of fuel! Mission failed.")
            break
        
        # Get allowable actions from environment
        allowable_actions = env.actions(agent_state)
        
        # Agent chooses action
        action = agent.choose_action(env)
        
        # Convert action to uppercase if it's a movement action
        if action in ['up', 'down', 'left', 'right']:
            env_action = action.upper()
        else:
            env_action = action.upper() if action in ['scan', 'collect', 'dock'] else None
        
        # Execute action if it's allowed
        if env_action and env_action in allowable_actions:
            print(f"Agent chooses action: {action}")
            
            # Update agent state through environment
            result = env.do_action(agent_state, env_action)
            agent_state = result["agent_state"]
            
            # Update agent attributes
            agent.location = agent_state["position"]
            agent.fuel = agent_state["fuel"]
            agent.health = agent_state["health"]
            agent.resources = agent_state["collected_resources"]
            agent.mapped_percentage = agent_state["covered_map_percentage"]
            agent.memory.update({cell: UNEXPLORED for cell in agent_state["explored_cells"]})
            
            # Handle specific action feedback
            if action == 'collect':
                print(f"Resources after collection: {agent.resources}")
            elif action == 'dock':
                print(f"Fuel after docking: {agent.fuel}")
            elif action == 'scan':
                print(f"New mapped percentage: {agent.mapped_percentage:.1f}%")
        else:
            print(f"Action {action} not allowed!")
        
        # Update environment
        env.update_env(agent_state)
        
        current_step += 1
    
    if current_step >= max_steps:
        print("\nMaximum steps reached! Mission incomplete.")
    
    print("\nFinal status:")
    print(f"Steps taken: {current_step}")
    print(f"Health: {agent.health}, Fuel: {agent.fuel}")
    print(f"Resources collected: {agent.resources}")
    print(f"Percentage mapped: {agent.mapped_percentage:.1f}%")
    print(f"At endpoint: {agent.location == env.end_position}")

if __name__ == "__main__":
    main()