from abc import ABC, abstractmethod
from typing import Tuple, List, Optional, Dict, Any


class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(self, name: str = "Agent") -> None:
        self.name: str = name
        self.position: Optional[Tuple[int, int]] = None
        self.items_collected: int = 0
        self.steps_taken: int = 0
        self.has_reached_goal: bool = False
    
    @abstractmethod
    def decide_move(self, possible_moves: List[Tuple[int, int]], grid_info: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """Decide the next move based on available options and grid information."""
        pass
    
    def reset(self) -> None:
        """Reset agent state for a new episode."""
        self.position = None
        self.items_collected = 0
        self.steps_taken = 0
        self.has_reached_goal = False