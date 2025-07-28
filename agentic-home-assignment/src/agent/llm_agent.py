import re
from typing import Tuple, List, Optional, Dict, Any
from .base_agent import BaseAgent
from .simple_agent import SimpleAgent
from ..llm.gemini_llm import GeminiLLM
from ..llm.llm_interface import LLMInterface


class LLMAgent(BaseAgent):
    """LLM-powered agent that uses external LLM for decision-making."""

    def __init__(self,
                 name: str = "LLMAgent",
                 llm_provider: Optional[LLMInterface] = GeminiLLM(),
                 fallback_agent: Optional[BaseAgent] = None):
        super().__init__(name)

        # LLM provider
        self.llm: LLMInterface = llm_provider or GeminiLLM()

        # Fallback agent
        self.fallback_agent = fallback_agent or SimpleAgent()

        # Agent state
        self.visit_count: Dict[Tuple[int, int], int] = {} # maps visited pos to the number of times visited
        self.context: List[Dict[str, Any]] = [] # summary of the previous llm responses

    def decide_move(self,
                    possible_moves: List[Tuple[int, int]],
                    grid_info: Dict[str, Any],
                    verbose: bool = True) -> Optional[Tuple[int, int]]:
        """Make a move decision using LLM reasoning."""

        if not possible_moves:
            return None

        # Update visit tracking
        curr_pos = grid_info["agent_position"]
        self.visit_count[curr_pos] = self.visit_count.get(curr_pos, 0) + 1

        try:
            # Build and send prompt
            prompt = self._create_prompt(grid_info, possible_moves)
            response = self.llm.query(prompt)

            if verbose:
                print(f"LLM response:\n{response}\n")

            # Parse response
            move_index, summary = self._parse_llm_response(response)

            if move_index is None or not (0 <= move_index < len(possible_moves)):
                raise ValueError(f"Invalid move index: {move_index}")

            # Record decision
            chosen_move = possible_moves[move_index]
            self._record_decision(chosen_move, summary)
            # move_analysis = self.get_move_analysis(possible_moves, obstacles, items, goal_pos)

            return chosen_move

        except Exception as e:
            print("Error: ")
            if verbose:
                print(f"Error: {e}. Falling back to simple strategy.")

            # Fallback to simple agent
            fallback_move = self.fallback_agent.decide_move(possible_moves, grid_info)
            if fallback_move:
                self._record_decision(fallback_move, "Fallback decision due to error")

            return fallback_move

    def _create_prompt(self, grid_info: Dict[str, Any], possible_moves: List[Tuple[int, int]]) -> str:
        """Create the prompt for the LLM."""
        agent_pos = grid_info["agent_position"]
        goal_pos = grid_info["goal_position"]
        obstacles = grid_info.get("obstacles_positions", [])
        items = grid_info.get("items_positions", [])
        items_collected = grid_info["items_collected"]
        items_total = items_collected + len(items)

        context_str = self._get_context_str()
        possible_moves_str = self._get_possible_moves_str(possible_moves)

        prompt = f"""You are an intelligent agent that can navigate through a grid-based world.
Your goal is to collect items, and reach a target goal efficiently. Positions are given in (x, y) coordinates.
GOAL: Get the highest score by collecting items and reaching the goal efficiently.
You are scored based on: Goal Reached Bonus + Items Collected percentage + Efficiency Bonus

CURRENT STATE:
- You are at: {agent_pos}
- Goal is at: {goal_pos}
- Items location: {items}
- Items collected: {items_collected}/{items_total}
- Obstacles found at: {obstacles}

PREVIOUS CHOSEN MOVES:
{context_str}
YOUR OPTIONS:
{possible_moves_str}

INSTRUCTIONS:
1. Prioritize collecting items over reaching the goal, especially clusters of items
2. Collect items when they are accessible with moderate effort
3. You cannot pass through obstacles, you will need to pass around them
4. Avoid getting trapped in dead ends, corners, or making excessive backtracking

Explain your thought process
Write a short summary of your decision between <summary> and </summary> tags. The summary must start with "The move (x,y) was chosen because...". If your goal is to aim towards a cluster or avoiding certain cells, mention them.
write the number of the final answer with: <move>NUMBER</move>"""

        return prompt

    def _get_possible_moves_str(self, possible_moves: List[Tuple[int, int]]) -> str:
        """Format possible moves as a numbered list for LLM selection."""
        moves_str = ""
        for i, move in enumerate(possible_moves):
            visit_count = self.visit_count.get(move, 0)
            moves_str += f"{i + 1}. Move to {move} (visited {visit_count} times)\n"
        return moves_str

    def _get_context_str(self) -> str:
        """Format recent decisions context."""
        if not self.context:
            return ""

        context_str = "RECENT DECISIONS:\n"
        for entry in self.context[-5:]:  # Show last 5 decisions
            context_str += f"Step {entry['step']}: Moved to {entry['move']} - {entry['reasoning']}\n"
        context_str += "\n"
        return context_str

    def _parse_llm_response(self, text: str) -> Tuple[Optional[int], Optional[str]]:
        """
        Extract the move number and summary from the agent's response text.

        Returns:
            tuple: (move_index, summary) where both can be None if not found
        """
        move_index = None
        summary = None

        # Extract move number from <move>NUMBER</move>
        try:
            move_match = re.search(r'<move>(\d+)</move>', text, re.IGNORECASE)
            if move_match:
                move_index = int(move_match.group(1)) - 1  # Convert to 0-based index
        except (ValueError, AttributeError):
            pass

        # Extract summary from <summary>...</summary>
        try:
            summary_match = re.search(r'<summary>(.*?)</summary>', text, re.IGNORECASE | re.DOTALL)
            if summary_match:
                summary = summary_match.group(1).strip()
                if not summary:
                    summary = None
        except AttributeError:
            pass

        return move_index, summary

    def _record_decision(self, move: Tuple[int, int], reasoning: str) -> None:
        """Record a decision in the context history."""
        context_entry = {
            'step': len(self.context) + 1,
            'move': move,
            'reasoning': reasoning if reasoning else "No reasoning provided"
        }
        self.context.append(context_entry)


    def get_move_analysis(self, possible_moves, obstacles, items, goal_pos):
        move_info = []

        for i, move in enumerate(possible_moves):
            x, y = move

            nearby_obstacles = []
            nearby_items = []
            goal_info = None

            # Check 3-cell radius around this move
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    if dx == 0 and dy == 0:  # Skip the move position itself
                        continue

                    check_pos = (x + dx, y + dy)

                    if check_pos in obstacles:
                        direction = self.get_direction_name(dx, dy)
                        nearby_obstacles.append(direction)

                    elif check_pos in items:
                        direction = self.get_direction_name(dx, dy)
                        distance = abs(dx) + abs(dy)
                        nearby_items.append(f"{direction} ({distance} steps)")

                    elif check_pos == goal_pos:
                        direction = self.get_direction_name(dx, dy)
                        distance = abs(dx) + abs(dy)
                        goal_info = f"{direction} ({distance} steps)"

            # Build description for this move
            description = [f"Move {i + 1} to {move}:"]

            if goal_info:
                description.append(f"  Goal is {goal_info}")

            if nearby_items:
                description.append(f"  Items: {', '.join(nearby_items)}")

            if nearby_obstacles:
                description.append(f"  Obstacles: {', '.join(nearby_obstacles)}")
            else:
                description.append("  No obstacles nearby - open area")

            move_info.append("\n".join(description))

        return "\n\n".join(move_info)

    def get_direction_name(self, dx, dy):
        """Convert relative coordinates to direction names"""
        if dx == 0 and dy < 0:
            return "NORTH"
        elif dx == 0 and dy > 0:
            return "SOUTH"
        elif dx < 0 and dy == 0:
            return "WEST"
        elif dx > 0 and dy == 0:
            return "EAST"
        elif dx < 0 and dy < 0:
            return "NORTHWEST"
        elif dx > 0 and dy < 0:
            return "NORTHEAST"
        elif dx < 0 and dy > 0:
            return "SOUTHWEST"
        elif dx > 0 and dy > 0:
            return "SOUTHEAST"
        else:
            return f"({dx},{dy})"
    def reset(self) -> None:
        """Reset agent state for a new episode."""
        super().reset()
        self.visit_count.clear()
        self.context.clear()
        if self.fallback_agent:
            self.fallback_agent.reset()