import pygame
import sys
import random
import time
from SpaceEnvironment import SpaceEnvironment
from SpaceEnvironment import EMPTY, AGENT, PLANET, METEOR, SPACE_STATION, NEBULA, RADIATION_ZONE, UNEXPLORED, END
from Spacecraft import Agent  # Import the intelligent agent

# Initialize Pygame
pygame.init()

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
DARK_BLUE = (25, 25, 112)

# Game settings
GRID_SIZE = (20, 20)
CELL_SIZE = 30
SCREEN_WIDTH = GRID_SIZE[0] * CELL_SIZE + 300  # Wider info panel for agent info
SCREEN_HEIGHT = GRID_SIZE[1] * CELL_SIZE

# Set up display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Game")
clock = pygame.time.Clock()

# Font
font = pygame.font.SysFont("Arial", 16)

class AutoSpaceGUI:
    def __init__(self):
        self.env = SpaceEnvironment(grid=GRID_SIZE)
        self.running = True
        self.auto_play = False
        self.step_delay = 0.2  # Time between steps in seconds
        self.last_step_time = 0
        self.damage_flash = 0  # Counter for damage visual effect
        self.meteor_highlights = []  # List for meteor highlighting
        self.highlight_timer = 0  # Timer for meteor highlights
        self.reset_game()
        
    def reset_game(self):
        self.env.initialize_env()
        self.agent_state = {
            "position": self.env.starting_position,
            "fuel": 100,
            "health": 100,
            "collected_resources": {"water": 0, "minerals": 0, "oxygen": 0},
            "explored_cells": {self.env.starting_position},
            "covered_map_percentage": 0.0
        }
        
        # Initialize the intelligent agent
        initial_agent_info = {
            'resource_goals': self.env.resource_goals
        }        
            
        # Create the agent
        self.agent = Agent(initial_agent_info, self.env.grid_size[0], 
                         location=self.env.starting_position)
                          
        # Do an initial scan to build the agent's knowledge
        result = self.env.do_action(self.agent_state, "SCAN")
        self.agent_state = result["agent_state"]
        percepts = result["percepts"]
        self.agent.sense(self.agent_state["position"], self.env)
        
        # Sync agent properties with agent_state
        self.agent.location = self.agent_state["position"]
        self.agent.fuel = self.agent_state["fuel"]
        self.agent.health = self.agent_state["health"]
        self.agent.resources = self.agent_state["collected_resources"].copy()
        
        self.last_health = 100  # Track health changes
        self.game_over = False
        self.timesteps = 0
        self.success = False
        self.last_action = None
        
    def draw_grid(self):
        # Draw background
        grid_area = pygame.Rect(0, 0, GRID_SIZE[0] * CELL_SIZE, GRID_SIZE[1] * CELL_SIZE)
        pygame.draw.rect(screen, DARK_BLUE, grid_area)
        
        # Draw damage flash effect
        if self.damage_flash > 0:
            # Create a semi-transparent red overlay when taking damage
            damage_surface = pygame.Surface((GRID_SIZE[0] * CELL_SIZE, GRID_SIZE[1] * CELL_SIZE), pygame.SRCALPHA)
            flash_alpha = min(120, self.damage_flash * 4)  # Max 120 alpha, fading out
            damage_surface.fill((255, 0, 0, flash_alpha))  # Red with alpha
            screen.blit(damage_surface, (0, 0))
            self.damage_flash -= 1
        
        # Draw grid lines
        for x in range(0, GRID_SIZE[0] * CELL_SIZE + 1, CELL_SIZE):
            pygame.draw.line(screen, WHITE, (x, 0), (x, GRID_SIZE[1] * CELL_SIZE), 1)
        for y in range(0, GRID_SIZE[1] * CELL_SIZE + 1, CELL_SIZE):
            pygame.draw.line(screen, WHITE, (0, y), (GRID_SIZE[0] * CELL_SIZE, y), 1)
        
        # Draw entities
        for row in range(GRID_SIZE[0]):
            for col in range(GRID_SIZE[1]):
                entity = self.env.grid[row, col]
                x = col * CELL_SIZE
                y = row * CELL_SIZE
                
                pos = (row, col)
                if pos in self.agent_state["explored_cells"]:
                    if entity == EMPTY:
                        pass  # Empty space
                    elif entity == AGENT:
                        pygame.draw.circle(screen, GREEN, (x + CELL_SIZE//2, y + CELL_SIZE//2), CELL_SIZE//2 - 5)
                    elif entity == PLANET:
                        pygame.draw.circle(screen, BLUE, (x + CELL_SIZE//2, y + CELL_SIZE//2), CELL_SIZE//2 - 5)
                    elif entity == METEOR:
                        # Bright orange-red color that stands out more
                        meteor_color = (255, 80, 0)
                        
                        # Draw a filled meteor (larger triangle)
                        pygame.draw.polygon(screen, meteor_color, [
                            (x + CELL_SIZE//2, y + 3),                # Top point
                            (x + 3, y + CELL_SIZE - 3),               # Bottom left
                            (x + CELL_SIZE - 3, y + CELL_SIZE - 3)    # Bottom right
                        ])
                        
                        # Add white outline for better visibility
                        pygame.draw.polygon(screen, WHITE, [
                            (x + CELL_SIZE//2, y + 3),
                            (x + 3, y + CELL_SIZE - 3),
                            (x + CELL_SIZE - 3, y + CELL_SIZE - 3)
                        ], 2)  # 2-pixel outline
                        
                        # Add a small dot in the center for extra visibility
                        pygame.draw.circle(screen, WHITE, (x + CELL_SIZE//2, y + CELL_SIZE//2), 3)
                    elif entity == SPACE_STATION:
                        pygame.draw.rect(screen, ORANGE, (x + 5, y + 5, CELL_SIZE - 10, CELL_SIZE - 10))
                    elif entity == NEBULA:
                        pygame.draw.circle(screen, PURPLE, (x + CELL_SIZE//2, y + CELL_SIZE//2), CELL_SIZE//2 - 5, 2)
                    elif entity == RADIATION_ZONE:
                        pygame.draw.rect(screen, YELLOW, (x + 5, y + 5, CELL_SIZE - 10, CELL_SIZE - 10), 2)
                    elif entity == END:
                        pygame.draw.rect(screen, WHITE, (x + 5, y + 5, CELL_SIZE - 10, CELL_SIZE - 10))
                else:
                    # Unexplored area
                    pygame.draw.rect(screen, BLACK, (x + 1, y + 1, CELL_SIZE - 2, CELL_SIZE - 2))
        
        # Draw meteor highlights if active
        if self.highlight_timer > 0:
            for pos in self.meteor_highlights:
                row, col = pos
                x = col * CELL_SIZE
                y = row * CELL_SIZE
                
                # Draw a flashing highlight around the meteor
                if self.highlight_timer % 10 < 5:  # Flash every 5 frames
                    pygame.draw.rect(screen, (255, 255, 0), (x, y, CELL_SIZE, CELL_SIZE), 3)  # Yellow highlight
                    
                    # Draw an arrow pointing to the meteor
                    pygame.draw.polygon(screen, (255, 255, 0), [
                        (x + CELL_SIZE//2, y - 10),         # Arrow tip
                        (x + CELL_SIZE//2 - 5, y - 5),      # Left corner
                        (x + CELL_SIZE//2 + 5, y - 5)       # Right corner
                    ])
            
            # Decrease the timer
            self.highlight_timer -= 1
            
        # Draw current target if it exists
        if hasattr(self.agent, 'current_target') and self.agent.current_target:
            target_row, target_col = self.agent.current_target
            tx = target_col * CELL_SIZE
            ty = target_row * CELL_SIZE
            
            # Draw a cyan highlight around the target
            pygame.draw.rect(screen, (0, 255, 255), (tx, ty, CELL_SIZE, CELL_SIZE), 3)
    
    def draw_info(self):
        # Info panel position
        panel_x = GRID_SIZE[0] * CELL_SIZE
        
        # Draw panel background
        panel_rect = pygame.Rect(panel_x, 0, 300, SCREEN_HEIGHT)
        pygame.draw.rect(screen, BLACK, panel_rect)
        
        # Basic info
        y_pos = 20
        info_items = [
            f"Health: {self.agent_state['health']}",
            f"Fuel: {self.agent_state['fuel']}",
            f"Water: {self.agent_state['collected_resources']['water']}/{self.env.resource_goals['water']}",
            f"Minerals: {self.agent_state['collected_resources']['minerals']}/{self.env.resource_goals['minerals']}",
            f"Oxygen: {self.agent_state['collected_resources']['oxygen']}/{self.env.resource_goals['oxygen']}",
            f"Map: {self.agent_state['covered_map_percentage']:.1f}%/{self.env.mapping_goal_percentage}%",
            f"Step: {self.timesteps}",
            "",
            f"Last Action: {self.last_action}",
        ]
        
        # Agent status if available
        if hasattr(self.agent, 'last_decision_reason'):
            info_items.append(f"Agent Decision: {self.agent.last_decision_reason}")
        
        if hasattr(self.agent, 'current_target'):
            info_items.append(f"Current Target: {self.agent.current_target}")
            
        info_items.extend([
            "",
            "Controls:",
            "R - Reset Game",
            "A - Start Auto Play",
            "S - Stop Auto Play",
            "M - Highlight Meteors"
        ])
        
        for item in info_items:
            text = font.render(item, True, WHITE)
            screen.blit(text, (panel_x + 10, y_pos))
            y_pos += 25
        
        # Game over message
        if self.game_over:
            game_status = self.env.is_game_over(self.agent_state)
            
            if self.agent_state["position"] == self.env.end_position:
                text = font.render("REACHED END POSITION!", True, GREEN)
                screen.blit(text, (panel_x + 10, y_pos))
                y_pos += 25
                
            if game_status["is_map_covered"]:
                text = font.render("MAP COVERAGE COMPLETE!", True, GREEN)
            else:
                text = font.render(f"MAP COVERAGE: {self.agent_state['covered_map_percentage']:.1f}%/{self.env.mapping_goal_percentage}%", True, RED)
            screen.blit(text, (panel_x + 10, y_pos))
            y_pos += 25
            
            if game_status["is_resources_met"]:
                text = font.render("RESOURCE GOALS MET!", True, GREEN)
            else:
                text = font.render("RESOURCE GOALS NOT MET", True, RED)
            screen.blit(text, (panel_x + 10, y_pos))
            y_pos += 25
            
            if self.agent_state["health"] <= 0:
                text = font.render("AGENT DIED", True, RED)
                screen.blit(text, (panel_x + 10, y_pos))
                y_pos += 25
                
            if self.agent_state["fuel"] <= 0:
                text = font.render("OUT OF FUEL", True, RED)
                screen.blit(text, (panel_x + 10, y_pos))
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                # Game controls
                if event.key == pygame.K_r:
                    self.reset_game()
                    self.auto_play = False
                elif event.key == pygame.K_a and not self.game_over:
                    # Start auto play
                    self.auto_play = True
                elif event.key == pygame.K_s:
                    # Stop auto play
                    self.auto_play = False
                elif event.key == pygame.K_m:  # 'M' key to highlight meteors
                    # Create a list to track meteor positions for debugging
                    self.meteor_highlights = []
                    meteor_count = 0
                    
                    # Find all meteor positions
                    for row in range(GRID_SIZE[0]):
                        for col in range(GRID_SIZE[1]):
                            if self.env.grid[row, col] == METEOR:
                                meteor_count += 1
                                self.meteor_highlights.append((row, col))
                                # Add to explored cells so they're visible
                                self.agent_state["explored_cells"].add((row, col))
                    
                    print(f"Found {meteor_count} meteors at positions: {self.meteor_highlights}")
                    
                    # Set a timer to display highlights for 3 seconds
                    self.highlight_timer = 90  # 90 frames at 30 FPS = 3 seconds
    
    def perform_action(self, action):
        self.last_action = action
        result = self.env.do_action(self.agent_state, action)
        self.agent_state = result["agent_state"]
        percepts = result["percepts"]
        
        # Update agent's memory if we got percepts
        if percepts:
            self.agent.sense(self.agent_state["position"], self.env)
            
        
        self.env.update_env(self.agent_state)
        self.timesteps += 1
        
        game_status = self.env.is_game_over(self.agent_state)
        self.game_over = game_status["is_game_over"]
        
        # Check if mission is successful
        if self.game_over:
            if game_status["is_map_covered"] and game_status["is_resources_met"]:
                self.success = True
            else:
                self.success = False
    
    def step_game(self):
        if not self.game_over:
            allowed_actions = self.env.actions(self.agent_state)
            
            # Update agent properties from agent_state
            self.agent.location = self.agent_state["position"]
            self.agent.fuel = self.agent_state["fuel"]
            self.agent.health = self.agent_state["health"]
            self.agent.resources = self.agent_state["collected_resources"].copy()
            
            # Use the intelligent agent to choose an action
            action = self.agent.choose_action(self.env, allowed_actions)
            self.perform_action(action)
    
    def run(self):
        while self.running:
            # Track health changes to show damage effects
            current_health = self.agent_state["health"]
            if current_health < self.last_health:
                # Health decreased - show damage effect
                damage_amount = self.last_health - current_health
                self.damage_flash = 30  # Flash for 30 frames
                print(f"Agent took {damage_amount} damage! Health: {current_health}")
            self.last_health = current_health
            
            self.handle_events()
            
            # Auto step logic
            current_time = time.time()
            if self.auto_play and not self.game_over and current_time - self.last_step_time > self.step_delay:
                self.step_game()
                self.last_step_time = current_time
            
            screen.fill(BLACK)
            self.draw_grid()
            self.draw_info()
            
            pygame.display.flip()
            clock.tick(30)
        
        pygame.quit()
        sys.exit()

# Run the game
if __name__ == "__main__":
    game = AutoSpaceGUI()
    game.run()