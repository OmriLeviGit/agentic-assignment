import random
import math
from typing import Tuple, List, Optional, Dict, Any
from .base_agent import BaseAgent

class SimpleAgent(BaseAgent):
    """Simple rule-based agent for comparison."""
    
    def __init__(self, name: str = "SimpleAgent") -> None:
        super().__init__(name)
    
    def decide_move(self, possible_moves: List[Tuple[int, int]], grid_info: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """Simple decision-making logic."""
        if not possible_moves:
            return None
        
        current_pos: Optional[Tuple[int, int]] = grid_info.get("agent_position")
        goal_pos: Optional[Tuple[int, int]] = grid_info.get("goal_position")
        items_positions: List[Tuple[int, int]] = grid_info.get("items_positions", [])
        
        if not current_pos or not goal_pos:
            return random.choice(possible_moves)
        
        # Collect items if possible
        for move in possible_moves:
            if move in items_positions:
                return move
        
        # Move towards goal
        best_move: Tuple[int, int] = possible_moves[0]
        best_distance: float = float('inf')
        
        for move in possible_moves:
            distance: int = abs(move[0] - goal_pos[0]) + abs(move[1] - goal_pos[1])
            if distance < best_distance:
                best_distance = distance
                best_move = move
        
        return best_move