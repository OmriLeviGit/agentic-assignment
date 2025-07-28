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
        self.map = {}

    def decide_move(self, possible_moves: List[Tuple[int, int]], grid_info: Dict[str, Any]) -> Optional[Tuple[int, int]]:

        if not possible_moves:
            return None

        prompt: str = self._create_prompt(grid_info, possible_moves)

        # Add the current position to the path
        curr_pos = grid_info["agent_position"]

        self.path.append(curr_pos)
        self.map[curr_pos] = self.map.get(curr_pos, 0) + 1

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
            moves_str += f"{i + 1}. Move to {move} (visited {self.map.get(agent_pos, 0)} times)\n"

        move_analysis = self.get_surroundings_info(agent_pos, obstacles, items, goal_pos)

        prompt = f"""You are an intelligent agent that can navigate through a grid-based world.
Your goal is to collect items, and reach a target goal efficiently. Position is given in (x, y) coordinates.
GOAL: Get the highest score by collecting items and reaching the goal efficiently.
You are scored based on: Goal Reached Bonus + Items Collected percentage + Efficiency Bonus

CURRENT STATE:
- You are at: {agent_pos}
- Goal is at: {goal_pos}
- Items location: {items}
- Items collected: {items_collected}/{items_total}
- Obstacles: {obstacles}
- Path taken: {self.path} 

YOUR OPTIONS:
{moves_str}

Additional info:
{move_analysis}

INSTRUCTIONS:
1. Prioritize collecting items over reaching the goal, especially clusters of items
2. Collect items when they are accessible with moderate effort
3. Pass obstacles by going around or between them.
4. Avoid visiting cells more than 3 times. Explore new areas, **even if surrounded by obstacles or moving further from the goal**

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

    def get_surroundings_info(self, agent_pos, obstacles, items, goal_pos):
        x, y = agent_pos

        nearby_obstacles = []
        nearby_items = []
        goal_info = None

        # Check 2-cell radius around agent
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if dx == 0 and dy == 0:  # Skip agent's current position
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

        # Build description
        description = []

        if goal_info:
            description.append(f"Goal is {goal_info}")

        if nearby_items:
            description.append(f"Items: {', '.join(nearby_items)}")

        if nearby_obstacles:
            description.append(f"Obstacles: {', '.join(nearby_obstacles)}")
        else:
            description.append("No obstacles nearby - open area")

        return "\n".join(description)

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