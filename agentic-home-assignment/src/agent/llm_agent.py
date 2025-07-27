import json

import requests
import re
from typing import Tuple, List, Optional, Dict, Any
from .base_agent import BaseAgent
import google.generativeai as genai


class LLMAgent(BaseAgent):
    def __init__(self, name: str = "LLMAgent"):
        super().__init__(name)
        self.ollama_url = "http://localhost:11434/api/generate"

        self.key = "AIzaSyBd5H8RN16q0_i9eOMMOzGgbZBbVAK1FtU"

        genai.configure(api_key="AIzaSyBd5H8RN16q0_i9eOMMOzGgbZBbVAK1FtU")
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def decide_move(self, possible_moves: List[Tuple[int, int]], grid_info: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        if not possible_moves:
            return None

        # Create strategic prompt
        prompt = self._create_prompt(grid_info, possible_moves)
        import re

        try:
            # Query TinyLlama
            response = self._query_llm(prompt)
            print("@@@\n", response, "\n@@@")

            # parsed = self._parse_response(response, possible_moves)

            return possible_moves[int(response)]

        except Exception as e:
            print(f"❌ LLM Error: {e}")

        # Fallback to simple strategy
        return self._fallback_move(possible_moves, grid_info)

    def _query_llm(self, prompt: str) -> str:
        """Query Ollama API exactly like the README example."""
        # payload = {
        #     "model": "tinyllama",
        #     "prompt": prompt,
        #     "stream": False,
        #     "options": {
        #         # "num_predict": 100,  # Very short response
        #         # "temperature": 0,  # Low randomness
        #         # "top_k": 0.3,  # Focused sampling
        #         # "stop": ["\n", "."]  # Stop at common delimiters
        #     }
        # }

        response = self.model.generate_content(prompt)

        # response = requests.post(self.ollama_url, json=payload)
        # response.raise_for_status()
        response = json.loads(response.candidates[0].content.parts[0].text)


        return response

#     def _create_prompt(self, grid_info, possible_moves):
#         agent_pos = grid_info["agent_position"]
#         goal_pos = grid_info["goal_position"]
#         items = grid_info.get("items_positions", [])
#         items_collected = grid_info["items_collected"]
#
#         # Create numbered list of moves
#         moves_str = ""
#         for i, move in enumerate(possible_moves):
#             moves_str += f"\n{i}. {move}"
#
#         return f"""
# Your task is to reach the goal.
# Current location: {agent_pos}
# Goal location: {goal_pos}
# Possible moves: {moves_str}
#
# what is the index of the best move? reply with the move index alone.
# """

    def _create_prompt(self, grid_info: Dict[str, Any], possible_moves: List[Tuple[int, int]]) -> str:
        agent_pos = grid_info["agent_position"]
        goal_pos = grid_info["goal_position"]
        items = grid_info.get("items_positions", [])
        obstacles = grid_info.get("obstacles_positions", [])
        steps_taken = grid_info["steps_taken"]
        items_collected = grid_info["items_collected"]

        goal_distance = abs(agent_pos[0] - goal_pos[0]) + abs(agent_pos[1] - goal_pos[1])

        prompt = f"""<instructions>
You are a strategic grid navigator. Your task is to collect items and reach goal efficiently.

<priorities>
1. Target HIGH CONCENTRATION item areas - but BEWARE of false clusters
2. Avoid dead ends and long corridors that trap you  
3. Check for obstacles that make items appear close but actually require long detours
4. Balance item collection vs goal completion based on progress
</priorities>

Your score will be calculated by:
Score = (Goal Reached Bonus) + (Items Collected %) + (Efficiency Bonus)

<situation>
Agent: {agent_pos} | Goal: {goal_pos} | Distance to goal: {goal_distance}
Items available: {items}
Items collected: {items_collected}
Steps taken so far: {steps_taken}
Obstacles (walls): {obstacles}
</situation>

The possible moves are: {possible_moves}
Reply with the index of the best move"""

        return prompt


    def _parse_response(self, response: str, possible_moves: List[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        """Extract coordinates from LLM response."""
        try:
            # Only look in response section
            if "<response>" not in response:
                return None

            response_section = response.split("<response>")[1]

            # Look for coordinates specifically after "I choose move:"
            if "I choose move:" in response_section:
                move_text = response_section.split("I choose move:")[1]
                coord_matches = re.findall(r'\((\d+),\s*(\d+)\)', move_text)
                if coord_matches:
                    x, y = int(coord_matches[0][0]), int(coord_matches[0][1])
                    move = (x, y)
                    if move in possible_moves:
                        return move

        except Exception as e:
            print(f"Parse error: {e}")

        return None

    def _fallback_move(self, possible_moves: List[Tuple[int, int]], grid_info: Dict[str, Any]) -> Tuple[int, int]:
        """Smart fallback when LLM fails."""
        agent_pos = grid_info["agent_position"]
        items = grid_info["items_positions"]
        goal_pos = grid_info["goal_position"]

        print("🔄 Using fallback strategy")

        # Prefer moves toward items, then toward goal
        best_move = possible_moves[0]
        # best_score = float('inf')
        #
        # for move in possible_moves:
        #     # Calculate score: distance to nearest valuable target
        #     targets = items + [goal_pos]
        #     score = min(abs(move[0] - target[0]) + abs(move[1] - target[1])
        #                 for target in targets)
        #
        #     if score < best_score:
        #         best_score = score
        #         best_move = move

        return best_move