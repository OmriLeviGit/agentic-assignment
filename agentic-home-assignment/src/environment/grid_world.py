import random
import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Union
from .entities import Agent, Item, Obstacle, Goal, CellType
from colorama import Fore, Back, Style, init

# Initialize colorama for cross-platform colored output
init()


class GridWorld:
    """2D grid world environment for the agent to navigate."""
    
    def __init__(self, width: int = 10, height: int = 10) -> None:
        self.width: int = width
        self.height: int = height
        self.grid: np.ndarray = np.full((height, width), CellType.EMPTY.value, dtype=str)
        
        # Entities
        self.agent: Optional[Agent] = None
        self.goal: Optional[Goal] = None
        self.items: List[Item] = []
        self.obstacles: List[Obstacle] = []
        
        # Game state
        self.game_over: bool = False
        self.victory: bool = False
    
    def is_valid_position(self, x: int, y: int) -> bool:
        """Check if position is within grid bounds."""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def is_position_free(self, x: int, y: int) -> bool:
        """Check if position is free (no obstacles or entities)."""
        if not self.is_valid_position(x, y):
            return False
        
        # Check for obstacles
        for obstacle in self.obstacles:
            if obstacle.position == (x, y):
                return False
        
        return True
    
    def get_cell_at(self, x: int, y: int) -> str:
        """Get the character representation of a cell."""
        # Agent takes priority in display
        if self.agent and self.agent.position == (x, y):
            return CellType.AGENT.value
        
        # Goal
        if self.goal and self.goal.position == (x, y):
            return CellType.GOAL.value
        
        # Items
        for item in self.items:
            if item.position == (x, y):
                return CellType.ITEM.value
        
        # Obstacles
        for obstacle in self.obstacles:
            if obstacle.position == (x, y):
                return CellType.OBSTACLE.value
        
        return CellType.EMPTY.value
    
    def place_agent(self, position: Optional[Tuple[int, int]] = None) -> bool:
        """Place agent at specified position or random free position."""
        if position is None:
            # Find random free position
            for _ in range(100):  # Max attempts
                x: int = random.randint(0, self.width-1)
                y: int = random.randint(0, self.height-1)
                if self.is_position_free(x, y):
                    position = (x, y)
                    break
            
            if position is None:
                return False
        
        if self.is_position_free(*position):
            self.agent = Agent(position)
            return True
        return False
    
    def place_goal(self, position: Optional[Tuple[int, int]] = None) -> bool:
        """Place goal at specified position or random free position."""
        if position is None:
            # Find random free position
            for _ in range(100):
                x: int = random.randint(0, self.width-1)
                y: int = random.randint(0, self.height-1)
                if self.is_position_free(x, y) and (not self.agent or self.agent.position != (x, y)):
                    position = (x, y)
                    break
            
            if position is None:
                return False
        
        if self.is_position_free(*position):
            self.goal = Goal(position)
            return True
        return False
    
    def add_obstacles(self, count: int, positions: Optional[List[Tuple[int, int]]] = None) -> None:
        """Add obstacles to the grid."""
        if positions:
            for pos in positions:
                if self.is_position_free(*pos):
                    self.obstacles.append(Obstacle(pos))
        else:
            placed: int = 0
            for _ in range(count * 10):  # Max attempts
                if placed >= count:
                    break
                
                x: int = random.randint(0, self.width-1)
                y: int = random.randint(0, self.height-1)
                if (self.is_position_free(x, y) and 
                    (not self.agent or self.agent.position != (x, y)) and
                    (not self.goal or self.goal.position != (x, y))):
                    self.obstacles.append(Obstacle((x, y)))
                    placed += 1
    
    def add_items(self, count: int, positions: Optional[List[Tuple[int, int]]] = None) -> None:
        """Add collectible items to the grid."""
        if positions:
            for pos in positions:
                if self.is_position_free(*pos):
                    self.items.append(Item(pos))
        else:
            placed: int = 0
            for _ in range(count * 10):  # Max attempts
                if placed >= count:
                    break
                
                x: int = random.randint(0, self.width-1)
                y: int = random.randint(0, self.height-1)
                if (self.is_position_free(x, y) and 
                    (not self.agent or self.agent.position != (x, y)) and
                    (not self.goal or self.goal.position != (x, y))):
                    self.items.append(Item((x, y)))
                    placed += 1
    
    def get_possible_moves(self) -> List[Tuple[int, int]]:
        """Get all possible moves for the agent."""
        if not self.agent:
            return []
        
        x: int
        y: int
        x, y = self.agent.position
        moves: List[Tuple[int, int]] = []
        
        # Four directions: up, down, left, right
        directions: List[Tuple[int, int]] = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        
        for dx, dy in directions:
            new_x: int = x + dx
            new_y: int = y + dy
            if self.is_position_free(new_x, new_y):
                moves.append((new_x, new_y))
        
        return moves
    
    def move_agent(self, new_position: Tuple[int, int]) -> bool:
        """Move agent to new position if valid."""
        if not self.agent or new_position not in self.get_possible_moves():
            return False
        
        self.agent.move_to(new_position)
        
        # Check for item collection
        for item in self.items[:]:  # Use slice to avoid modification during iteration
            if item.position == new_position:
                self.agent.collect_item()
                self.items.remove(item)
                break
        
        # Check for goal
        if self.goal and new_position == self.goal.position:
            self.agent.has_reached_goal = True
            self.victory = True
            self.game_over = True
        
        return True
    
    def get_grid_info(self) -> Dict[str, Any]:
        """Get current grid state information."""
        return {
            "agent_position": self.agent.position if self.agent else None,
            "goal_position": self.goal.position if self.goal else None,
            "items_positions": [item.position for item in self.items],
            "obstacles_positions": [obs.position for obs in self.obstacles],
            "items_collected": self.agent.items_collected if self.agent else 0,
            "steps_taken": self.agent.steps_taken if self.agent else 0
        }
    
    def render(self) -> str:
        """Render the grid as a colored string."""
        output: List[str] = []
        output.append(f"\n{Fore.CYAN}Grid World ({self.width}x{self.height}){Style.RESET_ALL}")
        output.append(f"{Fore.YELLOW}Steps: {self.agent.steps_taken if self.agent else 0}, "
                     f"Items: {self.agent.items_collected if self.agent else 0}{Style.RESET_ALL}\n")
        
        # Top border
        output.append("+" + "-" * (self.width * 2 + 1) + "+")
        
        for y in range(self.height):
            row: str = "| "
            for x in range(self.width):
                cell: str = self.get_cell_at(x, y)
                
                # Color coding
                colored_cell: str
                if cell == CellType.AGENT.value:
                    colored_cell = f"{Back.BLUE}{Fore.WHITE}{cell}{Style.RESET_ALL}"
                elif cell == CellType.GOAL.value:
                    colored_cell = f"{Back.GREEN}{Fore.WHITE}{cell}{Style.RESET_ALL}"
                elif cell == CellType.ITEM.value:
                    colored_cell = f"{Fore.YELLOW}{cell}{Style.RESET_ALL}"
                elif cell == CellType.OBSTACLE.value:
                    colored_cell = f"{Back.RED}{Fore.WHITE}{cell}{Style.RESET_ALL}"
                else:
                    colored_cell = cell
                
                row += colored_cell + " "
            
            row += "|"
            output.append(row)
        
        # Bottom border
        output.append("+" + "-" * (self.width * 2 + 1) + "+")
        
        if self.victory:
            output.append(f"\n{Back.GREEN}{Fore.WHITE}🎉 VICTORY! Goal reached! 🎉{Style.RESET_ALL}")
        
        return "\n".join(output)