import time
import os
import random
from typing import Optional, Dict, Any, Tuple, List, Union
from ..environment.grid_world import GridWorld
from ..agent.base_agent import BaseAgent


class Simulator:
    """Base simulator for running the grid world environment with agents."""
    
    def __init__(self, grid_size: Tuple[int, int] = (10, 10), max_steps: int = 100) -> None:
        self.width: int
        self.height: int
        self.width, self.height = grid_size
        self.max_steps: int = max_steps
        self.world: Optional[GridWorld] = None
        self.agent: Optional[BaseAgent] = None
        
    def setup_world(self, 
                   agent_pos: Optional[Tuple[int, int]] = None,
                   goal_pos: Optional[Tuple[int, int]] = None,
                   obstacle_positions: Optional[List[Tuple[int, int]]] = None,
                   item_positions: Optional[List[Tuple[int, int]]] = None,
                   num_obstacles: int = 5,
                   num_items: int = 3) -> None:
        """Set up the grid world with entities."""
        self.world = GridWorld(self.width, self.height)
        
        # Place agent
        if not self.world.place_agent(agent_pos):
            raise RuntimeError("Failed to place agent")
        
        # Place goal
        if not self.world.place_goal(goal_pos):
            raise RuntimeError("Failed to place goal")
        
        # Add obstacles
        if obstacle_positions:
            self.world.add_obstacles(0, obstacle_positions)
        else:
            self.world.add_obstacles(num_obstacles)
        
        # Add items
        if item_positions:
            self.world.add_items(0, item_positions)
        else:
            self.world.add_items(num_items)
    
    def run_simulation(self, agent: BaseAgent, 
                      delay: float = 1.0, 
                      clear_screen: bool = True,
                      verbose: bool = True) -> Dict[str, Any]:
        """Run the simulation with the given agent."""
        if not self.world:
            raise RuntimeError("World not set up. Call setup_world() first.")
        
        self.agent = agent
        self.agent.position = self.world.agent.position
        
        step: int = 0
        results: Dict[str, Any] = {
            "success": False,
            "steps_taken": 0,
            "items_collected": 0,
            "final_position": None,
            "path": [],
            "score": 0,
            "total_items_available": len(self.world.items)
        }
        
        if verbose:
            print(f"🚀 Starting simulation with {agent.name}")
            print(f"📍 Agent starts at: {self.world.agent.position}")
            print(f"🎯 Goal at: {self.world.goal.position}")
            print(f"💎 Items: {[item.position for item in self.world.items]}")
            print(f"🚧 Obstacles: {[obs.position for obs in self.world.obstacles]}")
            print("\n" + "="*50 + "\n")
        
        while step < self.max_steps and not self.world.game_over:
            if clear_screen:
                os.system('clear' if os.name == 'posix' else 'cls')
            
            if verbose:
                print(f"Turn {step + 1}:")
                print(self.world.render())
            
            # Get possible moves
            possible_moves: List[Tuple[int, int]] = self.world.get_possible_moves()
            if not possible_moves:
                if verbose:
                    print("❌ No possible moves available!")
                break
            
            # Agent decides on move
            grid_info: Dict[str, Any] = self.world.get_grid_info()
            chosen_move: Optional[Tuple[int, int]] = agent.decide_move(possible_moves, grid_info)
            
            if not chosen_move:
                if verbose:
                    print("❌ Agent couldn't decide on a move!")
                break
            
            if verbose:
                print(f"🤖 Agent moves from {self.world.agent.position} to {chosen_move}")
            
            # Execute move
            if self.world.move_agent(chosen_move):
                results["path"].append(chosen_move)
                step += 1
                
                if verbose and delay > 0:
                    time.sleep(delay)
            else:
                if verbose:
                    print("❌ Invalid move attempted!")
                break
        
        # Final results
        results.update({
            "success": self.world.victory,
            "steps_taken": self.world.agent.steps_taken,
            "items_collected": self.world.agent.items_collected,
            "final_position": self.world.agent.position,
            "total_items_available": results["total_items_available"]
        })
        
        # Calculate score
        results["score"] = self._calculate_score(results)
        
        if verbose:
            if clear_screen:
                os.system('clear' if os.name == 'posix' else 'cls')
            
            print(self.world.render())
            print("\n" + "="*50)
            print("📊 SIMULATION RESULTS")
            print("="*50)
            print(f"🎯 Goal reached: {'✅ YES' if results['success'] else '❌ NO'}")
            print(f"👣 Steps taken: {results['steps_taken']}")
            print(f"💎 Items collected: {results['items_collected']}")
            print(f"📍 Final position: {results['final_position']}")
            print(f"🛤️  Path length: {len(results['path'])}")
            print(f"📊 Score: {results['score']:.2f}")
            
            if step >= self.max_steps:
                print(f"⏰ Simulation ended: Maximum steps ({self.max_steps}) reached")
        
        return results
    
    def _calculate_score(self, results: Dict[str, Any]) -> float:
        """
        Calculate agent performance score normalized between 0-100.
        
        Scoring formula:
        - Base score: 30 points for reaching goal
        - Item bonus: +30 points per item collected (normalized by total items)
        - Step efficiency: up to 40 points based on step efficiency (increased weight)
        - All items bonus: +10 points if all items collected
        """
        score: float = 0.0
        
        # Base score for reaching goal (30% of total)
        if results["success"]:
            score += 30
        
        # Item collection bonus (up to 30% of total)
        items_collected: int = results["items_collected"]
        total_items: int = results["total_items_available"]
        if total_items > 0:
            item_score: float = (items_collected / total_items) * 30
            score += item_score
        
        # Step efficiency bonus (up to 40% of total - increased from 20%)
        # Reward fewer steps - use exponential decay to penalize excessive steps
        steps_taken: int = results["steps_taken"]
        if results["success"] and steps_taken > 0:
            # Assume reasonable baseline: grid diagonal + some exploration
            grid_size: int = max(self.width, self.height)
            baseline_steps: int = grid_size + total_items  # Rough estimate of reasonable steps
            
            # Calculate efficiency with more aggressive penalty for extra steps
            efficiency: float
            if steps_taken <= baseline_steps:
                # Perfect to good efficiency
                efficiency = 1.0
            else:
                # More aggressive exponential decay for steps beyond baseline
                excess_ratio: float = steps_taken / baseline_steps
                efficiency = max(0, 1.0 / (excess_ratio ** 1.5))  # Stronger penalty
            
            step_score: float = efficiency * 40  # Increased from 20 to 40
            score += step_score
        
        # All items collected bonus (10% of total)
        if items_collected == total_items and total_items > 0:
            score += 10
        
        # Ensure score is between 0 and 100
        return max(0, min(100, score))


class EasySimulator(Simulator):
    """Easy difficulty simulator - Small grid, few obstacles, straightforward path."""
    
    def __init__(self) -> None:
        super().__init__(grid_size=(5, 5), max_steps=25)
        self.difficulty: str = "easy"
    
    def setup_world(self, 
                   agent_pos: Optional[Tuple[int, int]] = None,
                   goal_pos: Optional[Tuple[int, int]] = None,
                   obstacle_positions: Optional[List[Tuple[int, int]]] = None,
                   item_positions: Optional[List[Tuple[int, int]]] = None,
                   **kwargs: Any) -> None:
        """Set up an easy world with minimal obstacles and clear paths."""
        # Default positions for easy mode
        if agent_pos is None:
            agent_pos = (0, 0)
        if goal_pos is None:
            goal_pos = (4, 4)
        
        # Predefined easy layout
        if obstacle_positions is None:
            obstacle_positions = [
                (2, 1), (1, 3), (3, 2)
            ]
        
        if item_positions is None:
            item_positions = [
                (3, 4), (1, 1), (0, 4)  # Top right, center, bottom left
            ]
        
        super().setup_world(
            agent_pos=agent_pos,
            goal_pos=goal_pos,
            obstacle_positions=obstacle_positions,
            item_positions=item_positions
        )
        
        print(f"🟢 Easy Mode: {self.width}x{self.height} grid, {len(obstacle_positions)} obstacles, {len(item_positions)} items")


class MediumSimulator(Simulator):
    """Medium difficulty simulator - Moderate grid, strategic obstacles, multiple paths."""
    
    def __init__(self) -> None:
        super().__init__(grid_size=(8, 8), max_steps=60)
        self.difficulty: str = "medium"
    
    def setup_world(self, 
                   agent_pos: Optional[Tuple[int, int]] = None,
                   goal_pos: Optional[Tuple[int, int]] = None,
                   obstacle_positions: Optional[List[Tuple[int, int]]] = None,
                   item_positions: Optional[List[Tuple[int, int]]] = None,
                   **kwargs: Any) -> None:
        """Set up a medium world with strategic obstacle placement."""
        # Default positions for medium mode
        if agent_pos is None:
            agent_pos = (0, 0)
        if goal_pos is None:
            goal_pos = (7, 7)
        
        # Predefined medium layout with strategic obstacles
        if obstacle_positions is None:
            obstacle_positions = [
                # Vertical barriers
                (2, 1), (2, 2), (2, 3),
                (5, 3), (5, 4), (5, 5),
                # Horizontal barriers
                (3, 5), (4, 5), (6, 5),
                # Scattered obstacles
                (1, 6), (6, 1), (4, 2), (7, 3)
            ]
        
        if item_positions is None:
            item_positions = [
                (1, 1), (3, 1), (6, 2), (3, 2), 
                (4, 4), (7, 6), (3, 7), 
            ]
        
        super().setup_world(
            agent_pos=agent_pos,
            goal_pos=goal_pos,
            obstacle_positions=obstacle_positions,
            item_positions=item_positions
        )
        
        print(f"🟡 Medium Mode: {self.width}x{self.height} grid, {len(obstacle_positions)} obstacles, {len(item_positions)} items")


class HardSimulator(Simulator):
    """Hard difficulty simulator - Large grid, complex maze-like structure, challenging paths."""
    
    def __init__(self) -> None:
        super().__init__(grid_size=(10, 10), max_steps=100)
        self.difficulty: str = "hard"
    
    def setup_world(self, 
                   agent_pos: Optional[Tuple[int, int]] = None,
                   goal_pos: Optional[Tuple[int, int]] = None,
                   obstacle_positions: Optional[List[Tuple[int, int]]] = None,
                   item_positions: Optional[List[Tuple[int, int]]] = None,
                   **kwargs: Any) -> None:
        """Set up a hard world with maze-like obstacle patterns."""
        # Default positions for hard mode
        if agent_pos is None:
            agent_pos = (0, 0)
        if goal_pos is None:
            goal_pos = (9, 9)
        
        # Reduced obstacle layout - still challenging but with guaranteed paths
        if obstacle_positions is None:
            obstacle_positions = [
                # Major vertical walls (reduced)
                (2, 1), (2, 2), (2, 3),
                (5, 2), (5, 3), (5, 4), (5, 5),
                
                # Major horizontal walls (reduced)
                (0, 6), (1, 6), (2, 6),
                (6, 3), (7, 3), (8 , 2),
                (3, 8), (4, 8), (5, 8),
                
                # Strategic obstacles (reduced)
                (1, 1), (1, 3), (8, 1),
                (3, 1), (6, 4),
                (8, 5), (9, 3),
                
                # Additional complexity (reduced)
                (4, 2), (6, 6), (7, 7)
            ]
        
        if item_positions is None:
            item_positions = [
                # Top right corner
                (9, 0), (8, 0), (9, 2),
                # Bottom left corner  
                (2, 8), (1, 9),
                # Scattered throughout the maze
                (3, 0), (6, 0), (9, 3),
                (0, 2), (4, 3), (9, 1),
                (3, 2), (3, 5), (6, 5),
                (4, 9), (0, 7)
            ]
        
        super().setup_world(
            agent_pos=agent_pos,
            goal_pos=goal_pos,
            obstacle_positions=obstacle_positions,
            item_positions=item_positions
        )
        
        print(f"🔴 Hard Mode: {self.width}x{self.height} grid, {len(obstacle_positions)} obstacles, {len(item_positions)} items")
    
    def _calculate_score(self, results: Dict[str, Any]) -> float:
        """Override scoring for hard mode - more emphasis on completion."""
        score: float = super()._calculate_score(results)
        
        # Bonus for completing hard mode
        if results["success"]:
            score += 5  # Extra 5 points for hard mode completion
        
        return min(100, score)


def get_simulator_by_difficulty(difficulty: str) -> Simulator:
    """Factory function to get the appropriate simulator based on difficulty level."""
    difficulty_clean: str = difficulty.lower().strip()
    
    if difficulty_clean == "easy":
        return EasySimulator()
    elif difficulty_clean == "medium":
        return MediumSimulator()
    elif difficulty_clean == "hard":
        return HardSimulator()
    else:
        raise ValueError(f"Invalid difficulty: {difficulty}. Must be 'easy', 'medium', or 'hard'")


# Legacy alias for backward compatibility
def create_simulator(difficulty: str = "medium") -> Simulator:
    """Create a simulator with specified difficulty level."""
    return get_simulator_by_difficulty(difficulty)