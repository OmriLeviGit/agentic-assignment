import re
from typing import Tuple, List, Optional, Dict, Any
from .base_agent import BaseAgent
from .simple_agent import SimpleAgent
from ..llm.gemini_llm import GeminiLLM
from ..llm.tiny_llama_llm import TinyLlamaLLM
from ..llm.llm_interface import LLMInterface


class LLMAgent(BaseAgent):
    """LLM-powered agent that uses external LLM for decision-making."""

    def __init__(self,
                 name: str = "LLMAgent",
                 llm_provider: Optional[LLMInterface] = None,
                 fallback_agent: Optional[BaseAgent] = None):
        super().__init__(name)

        # LLM provider
        self.llm: LLMInterface = self._setup_llm_with_fallback(llm_provider)

        # Fallback agent
        self.fallback_agent = fallback_agent or SimpleAgent()

        # Agent state
        self.visit_count: Dict[Tuple[int, int], int] = {} # maps visited pos to the number of times visited
        self.path = []
        self.context: List[Dict[str, Any]] = [] # summary of the previous llm responses

    def _setup_llm_with_fallback(self, llm_provider: Optional[LLMInterface]) -> LLMInterface:
        """Setup LLM with fallback chain: Custom -> Gemini -> Ollama"""

        # If a specific provider is given, try it first
        if llm_provider is not None:
            if llm_provider.is_available():
                return llm_provider

        # Try Gemini
        try:
            gemini = GeminiLLM()
            if gemini.is_available():
                print("Using Gemini LLM")
                return gemini
        except Exception as e:
            print(f"Gemini not available: {e}")

        # Fall back to tiny llama
        try:
            llama = TinyLlamaLLM()
            print("Using TinyLlama")
            return llama
        except Exception as e:
            print(f"Ollama setup failed: {e}")
            raise RuntimeError("No LLM providers available!")

    def decide_move(self, possible_moves: List[Tuple[int, int]], grid_info: Dict[str, Any],
                    verbose: bool = False) -> Optional[Tuple[int, int]]:
        """Make a move decision using LLM reasoning."""

        if not possible_moves:
            return None

        # Update visit tracking
        curr_pos = grid_info["agent_position"]
        self.visit_count[curr_pos] = self.visit_count.get(curr_pos, 0) + 1

        agent_pos = grid_info["agent_position"]
        items = grid_info.get("items_positions", [])

        # Check for close items within threshold distance
        close_items = self._get_close_items(agent_pos, items)

        if len(close_items) > 0:
            try:
                # Build and send prompt with close items - let LLM decide navigation
                prompt = self._create_prompt(grid_info, possible_moves, close_items)
                response = self.llm.query(prompt)

                if verbose:
                    print(f"LLM response:\n{response}\n")

                # Parse response
                move_index, summary = self._parse_llm_response(response)

                if move_index is None or not (0 <= move_index < len(possible_moves)):
                    raise ValueError(f"Invalid move index: {move_index}")

                # Record decision
                chosen_move = possible_moves[move_index]
                self.path.append(chosen_move)
                self._record_decision(chosen_move, summary)

                return chosen_move

            except Exception as e:
                print(f"Error: {e}. Falling back to simple strategy.")

        # Fallback to simple agent when no close items or on error
        fallback_move = self.fallback_agent.decide_move(possible_moves, grid_info)
        self.path.append(fallback_move)
        if fallback_move:
            self._record_decision(fallback_move, "Fallback decision - no close items or error")

        return fallback_move

    def _create_prompt(self, grid_info: Dict[str, Any], possible_moves: List[Tuple[int, int]],
                       close_items: List[Tuple[Tuple[int, int], int]]) -> str:
        """Create the prompt for the LLM with close items information."""
        agent_pos = grid_info["agent_position"]
        goal_pos = grid_info["goal_position"]
        obstacles = grid_info.get("obstacles_positions", [])
        items_collected = grid_info["items_collected"]

        # Extract just the positions and distances from close_items
        close_items_info = [(item[0], item[1]) for item in close_items]

        context_str = "PREVIOUSLY CHOSEN MOVES: " + self._get_context_str()
        possible_moves_str = "YOUR OPTIONS: " + self._get_possible_moves_str(possible_moves, close_items)

        prompt = f"""You are an intelligent agent navigating a grid-based world.
Your PRIMARY GOAL is to collect nearby items efficiently. The fallback system handles goal navigation.

COORDINATE SYSTEM:
- (0,0) is at the top-left corner of the grid
- x increases going RIGHT, y increases going DOWN
- You can move up/down/left/right to adjacent cells only

MOVEMENT RULES:
- Any position NOT listed in the obstacles is WALKABLE
- You can only choose from the provided possible moves
- All provided moves are guaranteed to be valid and within grid bounds

CURRENT STATE:
- You are at: {agent_pos}
- Goal is at: {goal_pos}
- Close items detected: {close_items_info}
- Obstacle positions: {obstacles}
- Items collected so far: {items_collected}

{context_str}

{possible_moves_str}

ANTI-LOOP STRATEGY:
⚠️ CRITICAL: Avoid revisiting recent positions to prevent getting stuck in loops!
- Your recent path: {self.path[-6:] if len(self.path) >= 6 else self.path}
- NEVER choose moves that go back to positions in your recent path
- If you see the same positions repeating in your path, you're in a loop

1. **Check for loops FIRST**: Will this move revisit a position from your recent path?
2. **Trace direct paths**: What sequence of moves would reach each item?
3. **Check obstacles**: Does any step land on an obstacle coordinate?
4. **Alternative routes**: Are there non-looping routes to items?

EFFICIENT ITEM COLLECTION STRATEGY:
🎯 Don't just grab the closest item - plan a smart collection route!
- Goal direction awareness: Goal is at {goal_pos}
- Collection order: Start with items FURTHEST from the goal, work toward the goal
- Avoid zigzagging: Don't collect item near goal, then backtrack to far items
- Think ahead: Which item should you collect LAST to minimize total travel?

DECISION CRITERIA:
1. **AVOID LOOPS**: Avoid moves in your recent path
2. **Explore new areas**: If items unreachable but you can explore new positions → do that
3. **Fallback**: If a loop is detected, or the current position was visited more than once in recent positions, or all possible moves appear in the recent recent path positions

ESCAPE STRATEGY:
If you're stuck in a corner or dead end:
- Look for moves to positions NOT in your recent path
- Choose moves that lead away from obstacle clusters
- Prioritize exploration over item collection to escape

<summary>The move (x,y) was chosen because... OR Fallback (-1) was chosen because...</summary>

<move>NUMBER</move> (0-{len(possible_moves) - 1} for moves, or -1 only if ALL moves revisit recent path)"""

        return prompt

    def _get_close_items(self, agent_pos: Tuple[int, int], items: List[Tuple[int, int]],
                         max_distance: int = 3) -> List[Tuple[Tuple[int, int], int]]:
        """Get items within Manhattan distance threshold."""
        close_items = []
        for item in items:
            distance = abs(item[0] - agent_pos[0]) + abs(item[1] - agent_pos[1])
            if distance <= max_distance:
                close_items.append((item, distance))

        return close_items

    def _get_possible_moves_str(self, possible_moves: List[Tuple[int, int]],
                                close_items: List[Tuple[Tuple[int, int], int]]) -> str:
        """Generate string representation of possible moves with item proximity info."""
        moves_info = []
        close_item_positions = {item[0] for item in close_items}

        for i, move in enumerate(possible_moves):
            move_str = f"{i}: Move to {move}"

            # Check if this move gets us to an item
            if move in close_item_positions:
                move_str += " (ITEM HERE!)"
            else:
                # Calculate how this move affects distance to close items
                item_distances = []
                for item_pos, original_dist in close_items:
                    new_dist = abs(move[0] - item_pos[0]) + abs(move[1] - item_pos[1])
                    item_distances.append(f"item{item_pos}:{new_dist}")

                if item_distances:
                    move_str += f" (distances to items: {', '.join(item_distances)})"

            moves_info.append(move_str)

        return "\n".join(moves_info)

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
                move_index = int(move_match.group(1))   # Convert to 0-based index
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

    def reset(self) -> None:
        """Reset agent state for a new episode."""
        super().reset()
        self.visit_count.clear()
        self.context.clear()
        if self.fallback_agent:
            self.fallback_agent.reset()