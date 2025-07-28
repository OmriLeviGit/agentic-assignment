import re
from typing import Tuple, List, Optional, Dict, Any
import requests
from requests.models import Response

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
            best_move_index = self._parse_llm_response(response)

            for pm in possible_moves:
                if str(pm) == best_move_index:
                    return pm

            raise ValueError("outside")

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

        prompt = f"""Instructions:
You are playing a grid game in turns. Each turn you can move to a neighboring cell.
GOAL: Get the highest score by collecting items and reaching the goal efficiently. Choose the best move.

CURRENT STATE:
- You are at: {agent_pos}
- you can only move to the following positions: {possible_moves}
- You want to reach to the Goal at: {goal_pos}
- Items collected: {items_collected}/{items_total}
- Obstacles to avoid: {obstacles}

Respond with the best move"""

        return prompt

    def _query_llm(self, prompt: str) -> str:
        """Query Ollama API exactly like the README example."""
        payload = {
            "model": "tinyllama",
            "prompt": prompt,
            "stream": False,
            "options": {
                # "num_predict": 100,  # Very short response
                # "temperature": 0,  # Low randomness
                # "top_k": 0.3,  # Focused sampling
                # "stop": ["\n", "."]  # Stop at common delimiters
            }
        }

        response = requests.post(self.ollama_url, json=payload)
        response.raise_for_status()

        return response.json()['response']

    def _parse_llm_response(self, response_text):
        """Extract move number from <move>NUMBER</move> tags."""
        # Look for <move>NUMBER</move> pattern
        move_match = re.search(r'\(\d+,\s*\d+\)', response_text, re.IGNORECASE)
        if move_match:
            try:
                move_num = move_match.group(0)
                return move_num
            except ValueError:
                raise ValueError(f"Invalid move number format: {move_match.group(1)}")

        raise ValueError("No valid <move>NUMBER</move> tag found in response")