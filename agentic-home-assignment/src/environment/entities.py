from enum import Enum
from typing import Tuple


class CellType(Enum):
    """Types of cells in the grid world."""
    EMPTY = "."
    OBSTACLE = "#"
    ITEM = "$"
    GOAL = "G"
    AGENT = "A"


class GridEntity:
    """Base class for entities in the grid world."""
    
    def __init__(self, position: Tuple[int, int], cell_type: CellType) -> None:
        self.position: Tuple[int, int] = position
        self.cell_type: CellType = cell_type
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.position})"


class Agent(GridEntity):
    """The agent entity that navigates the grid."""
    
    def __init__(self, position: Tuple[int, int]) -> None:
        super().__init__(position, CellType.AGENT)
        self.items_collected: int = 0
        self.steps_taken: int = 0
        self.has_reached_goal: bool = False
    
    def move_to(self, new_position: Tuple[int, int]) -> None:
        """Move the agent to a new position."""
        self.position = new_position
        self.steps_taken += 1
    
    def collect_item(self) -> None:
        """Collect an item."""
        self.items_collected += 1


class Item(GridEntity):
    """Collectible item in the grid."""
    
    def __init__(self, position: Tuple[int, int]) -> None:
        super().__init__(position, CellType.ITEM)


class Obstacle(GridEntity):
    """Obstacle that blocks movement."""
    
    def __init__(self, position: Tuple[int, int]) -> None:
        super().__init__(position, CellType.OBSTACLE)


class Goal(GridEntity):
    """Goal position the agent must reach."""
    
    def __init__(self, position: Tuple[int, int]) -> None:
        super().__init__(position, CellType.GOAL)