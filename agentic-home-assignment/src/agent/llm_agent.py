import re
from typing import Tuple, List, Optional, Dict, Any
from .simple_agent import SimpleAgent
import google.generativeai as genai


class LLMAgent(SimpleAgent):
    def __init__(self, name: str = "LLMAgent"):
        super().__init__(name)

        self.ollama_url = "http://localhost:11434/api/generate"
        self.key = "AIzaSyBd5H8RN16q0_i9eOMMOzGgbZBbVAK1FtU"

        genai.configure(api_key="AIzaSyBd5H8RN16q0_i9eOMMOzGgbZBbVAK1FtU")
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def decide_move(self, possible_moves: List[Tuple[int, int]], grid_info: Dict[str, Any]) -> Optional[Tuple[int, int]]:

        if not possible_moves:
            return None

        prompt: str = self._create_prompt(grid_info, possible_moves)

        try:
            response: str = self._query_llm(prompt)
            best_move_index: int = self._parse_llm_response(response)

            return possible_moves[best_move_index]

        except Exception as e:
            print(f"❌ LLM Error: {e}")
            # Fallback to the simple strategy
            return super().decide_move(possible_moves, grid_info)

    def _create_prompt(self, grid_info, possible_moves):
        agent_pos = grid_info["agent_position"]
        goal_pos = grid_info["goal_position"]
        obstacles = grid_info.get("obstacles_positions", [])
        items = grid_info.get("items_positions", [])
        items_collected = grid_info["items_collected"]
        items_total = items_collected + len(items)

        # Format possible moves as numbered list for LLM selection
        moves_str = ""
        for i, move in enumerate(possible_moves):
            # 1-index the moves
            moves_str += f"{i + 1}. Move to {move}\n"

        prompt = f"""MISSION: Maximize score = Goal Bonus + Number of Collected Items + Full Collection Bonus + Efficiency bonus
        
STATUS:
- Position: {agent_pos} | Goal: {goal_pos}
- Items: {items}/{items_total}
- Obstacles: {obstacles}

POSSIBLE MOVES:
{moves_str}

STRATEGY: Consider all factors - item collection efficiency, path to goal, obstacle avoidance.
Your objective should be to collect all items, but do take note that long corridors that require backtracking may not be as efficient

Return your choice in xml tags: <move>NUMBER</move>"""

        return prompt

    def _query_llm(self, prompt: str) -> str:
        """Query Ollama API exactly like the README example."""

        response = self.model.generate_content(prompt)
        response_text = response.candidates[0].content.parts[0].text

        return response_text

    def _parse_llm_response(self, response_text) -> int:
        """Extract move number from <move>NUMBER</move> tags."""
        # Look for <move>NUMBER</move> pattern
        move_match = re.search(r'<move>(\d+)</move>', response_text, re.IGNORECASE)
        if move_match:
            try:
                move_num = int(move_match.group(1))
                return move_num - 1  # Convert to 0-indexed
            except ValueError:
                raise ValueError(f"Invalid move number format: {move_match.group(1)}")

        raise ValueError("No valid <move>NUMBER</move> tag found in response")