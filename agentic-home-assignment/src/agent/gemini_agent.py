import re
from typing import Tuple, List, Optional, Dict, Any
from .simple_agent import SimpleAgent
import google.generativeai as genai

# A free test key with very restricting rate limits, would NEVER be here under normal circumstances
API_KEY = "AIzaSyBd5H8RN16q0_i9eOMMOzGgbZBbVAK1FtU"
genai.configure(api_key=API_KEY)

class LLMAgent(SimpleAgent):
    def __init__(self, name: str = "LLMAgent"):
        super().__init__(name)

        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')  # Gemini model

    def decide_move(self, possible_moves: List[Tuple[int, int]], grid_info: Dict[str, Any]) -> Optional[Tuple[int, int]]:

        if not possible_moves:
            return None

        prompt: str = self._create_prompt(grid_info, possible_moves)

        try:
            response: str = self._query_llm(prompt)
            print(response)
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

        prompt = f"""You are playing a grid game. Choose the best move.
GOAL: Get the highest score by collecting items and reaching the goal efficiently.

CURRENT STATE:
- You are at: {agent_pos}
- Goal is at: {goal_pos}
- Items collected: {items_collected}/{items_total}
- Obstacles to avoid: {obstacles}

YOUR OPTIONS:
{moves_str}

INSTRUCTIONS:
1. Collect items when possible
2. Move toward the goal
3. Avoid obstacles
4. Choose efficiently
5. Be decisive

Answer with: <move>NUMBER</move>"""

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