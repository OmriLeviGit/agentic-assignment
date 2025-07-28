import os
import re
from typing import Tuple, List, Optional, Dict, Any

from dotenv import load_dotenv, find_dotenv

from .simple_agent import SimpleAgent

import google.generativeai as genai

load_dotenv(find_dotenv())
API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=API_KEY)

class LLMAgent(SimpleAgent):
    def __init__(self, name: str = "LLMAgent"):
        super().__init__(name)

        self.model = genai.GenerativeModel('gemini-1.5-flash')  # Gemini model
        self.path = []    # All positions the agent had visited

    def decide_move(self, possible_moves: List[Tuple[int, int]], grid_info: Dict[str, Any]) -> Optional[Tuple[int, int]]:

        if not possible_moves:
            return None

        prompt: str = self._create_prompt(grid_info, possible_moves)

        # Add the current position to the path
        self.path.append(grid_info["agent_position"])

        try:
            response: str = self._query_llm(prompt)
            print(response)
            best_move_index: int = self._parse_llm_response(response)

            return possible_moves[best_move_index]  # Raises an error if the index is out of range

        except Exception as e:
            print(f"Error: {e}")
            # Fallback to the simple strategy
            return super().decide_move(possible_moves, grid_info)

    def _create_prompt(self, grid_info, possible_moves):
        agent_pos = grid_info["agent_position"]
        goal_pos = grid_info["goal_position"]
        obstacles = grid_info.get("obstacles_positions", [])
        items = grid_info.get("items_positions", [])
        items_collected = grid_info["items_collected"]
        items_total = items_collected + len(items)

        # Format possible moves as a 1-index numbered list for LLM selection
        moves_str = ""
        for i, move in enumerate(possible_moves):
            moves_str += f"{i + 1}. Move to {move}\n"

        # move_analysis = []
        # for i, move in enumerate(possible_moves):
        #     nearby_obstacles = [obs for obs in obstacles if self.calculate_distance(move, obs) <= 3]
        #     nearby_items = [item for item in items if self.calculate_distance(move, item) <= 3]
        #     move_analysis.append(
        #         f"Move {i + 1} to {move}: {len(nearby_obstacles)} obstacles nearby, {len(nearby_items)} items nearby")

        prompt = f"""You are an intelligent agent that can navigate through a grid-based world.
Your goal is to collect items, and reach a target goal efficiently. Position is given in (x, y) coordinates.
GOAL: Get the highest score by collecting items and reaching the goal efficiently.
You are scored based on: Goal Reached Bonus + Items Collected percentage + Efficiency Bonus

CURRENT STATE:
- You are at: {agent_pos}
- Goal is at: {goal_pos}
- Items location: {items}
- Items collected: {items_collected}/{items_total}
- Obstacles to avoid: {obstacles}
- Path taken so far: {self.path}

YOUR OPTIONS:
{moves_str}

INSTRUCTIONS:
1. Prioritize collecting items over reaching the goal, especially clusters of items
2. Collect items when they are accessible with moderate effort
3. You cannot pass through obstacles, you will need to pass around them
4. Avoid getting trapped in dead ends, corners, or making excessive backtracking
5. Move toward the goal if remaining items are too far (for example, opposite directions)

# Information: {move_analysis}

Explain your thought process, and write the number of the final answer with: <move>NUMBER</move>"""

        return prompt

    def _query_llm(self, prompt: str) -> str:
        """Query the LLM's API"""
        try:
            response = self.model.generate_content(prompt)
            response_text: str = response.candidates[0].content.parts[0].text
            return response_text

        except Exception as e:
            raise RuntimeError(f"Error querying LLM: {e}")

    def _parse_llm_response(self, response_text: str) -> int:
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

    def calculate_distance(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])