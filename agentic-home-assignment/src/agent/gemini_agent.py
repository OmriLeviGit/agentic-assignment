# import os
# import re
# from typing import Tuple, List, Optional, Dict, Any
#
# from dotenv import load_dotenv, find_dotenv
#
# from .simple_agent import SimpleAgent
#
# import google.generativeai as genai
#
# load_dotenv(find_dotenv())
# API_KEY = os.getenv('GEMINI_API_KEY')
# genai.configure(api_key=API_KEY)
#
# class LLMAgent(SimpleAgent):
#     def __init__(self, name: str = "LLMAgent"):
#         super().__init__(name)
#
#         self.model = genai.GenerativeModel('gemini-1.5-flash')  # Gemini model
#         self.visited_map = {}
#         self.context = []
#
#     def decide_move(self, possible_moves: List[Tuple[int, int]], grid_info: Dict[str, Any], verbose=True) -> Optional[Tuple[int, int]]:
#
#         if not possible_moves:
#             return None
#
#         prompt: str = self._create_prompt(grid_info, possible_moves)
#
#         # Add the current position to the path
#         curr_pos = grid_info["agent_position"]
#         self.visited_map[curr_pos] = self.visited_map.get(curr_pos, 0) + 1
#
#         try:
#             response: str = self._query_llm(prompt)
#
#             if verbose:
#                 print(response)
#
#             best_move_index, summary = self._parse_llm_response(response)
#
#             context_entry = {
#                 'step': len(self.context) + 1,
#                 'move': possible_moves[best_move_index] if best_move_index is not None else None,
#                 'reasoning': summary if summary is not None else "Summary was not parsed correctly"
#             }
#
#             self.context.append(context_entry)
#
#             return possible_moves[best_move_index]  # Raises an error if the index is out of range
#
#         except Exception as e:
#             print(f"Error: {e}")
#             # Fallback to the simple strategy
#             return super().decide_move(possible_moves, grid_info)
#
#     def _create_prompt(self, grid_info, possible_moves):
#         agent_pos = grid_info["agent_position"]
#         goal_pos = grid_info["goal_position"]
#         obstacles = grid_info.get("obstacles_positions", [])
#         items = grid_info.get("items_positions", [])
#         items_collected = grid_info["items_collected"]
#         items_total = items_collected + len(items)
#
#         context_str: str = self._get_context_str()
#         possible_moves_str: str = self._get_possible_moves_str(agent_pos, possible_moves)
#         # move_analysis = self.get_move_analysis(possible_moves, obstacles, items, goal_pos)
#
#         prompt = f"""You are an intelligent agent that can navigate through a grid-based world.
# Your goal is to collect items, and reach a target goal efficiently. Positions are given in (x, y) coordinates.
# GOAL: Get the highest score by collecting items and reaching the goal efficiently.
# You are scored based on: Goal Reached Bonus + Items Collected percentage + Efficiency Bonus
#
# CURRENT STATE:
# - You are at: {agent_pos}
# - Goal is at: {goal_pos}
# - Items location: {items}
# - Items collected: {items_collected}/{items_total}
# - Obstacles found at: {obstacles}
#
# PREVIOUS CHOSEN MOVES:
# {context_str}
# YOUR OPTIONS:
# {possible_moves_str}
#
# INSTRUCTIONS:
# 1. Prioritize collecting items over reaching the goal, especially clusters of items
# 2. Collect items when they are accessible with moderate effort
# 3. You cannot pass through obstacles, you will need to pass around them
# 4. Avoid getting trapped in dead ends, corners, or making excessive backtracking
#
# Explain your thought process
# Write a short summary of your decision between <summary> and </summary> tags. The summary must start with "The move (x,y) was chosen because...". If your goal is to aim towards a cluster or avoiding certain cells, mention them.
# write the number of the final answer with: <move>NUMBER</move>"""
#
#         return prompt
#
#     def _get_possible_moves_str(self, agent_pos, possible_moves):
#         """Format possible moves as a 1-index numbered list for LLM selection"""
#         moves_str = ""
#         for i, move in enumerate(possible_moves):
#             moves_str += f"{i + 1}. Move to {move} (visited {self.visited_map.get(agent_pos, 0)} times)\n"
#
#         return moves_str
#
#     def _get_context_str(self):
#         """Format possible moves as a 1-index numbered list for LLM selection"""
#         context_str = ""
#         if self.context:
#             context_str = "RECENT DECISIONS:\n"
#             for entry in self.context[-5:]:  # Show last 5 decisions
#                 context_str += f"Step {entry['step']}: Moved to {entry['move']} - {entry['reasoning']}\n"
#             context_str += "\n"
#
#         return context_str
#
#
#     def _query_llm(self, prompt: str) -> str:
#         """Query the LLM's API"""
#         try:
#             response = self.model.generate_content(prompt)
#             response_text: str = response.candidates[0].content.parts[0].text
#             return response_text
#
#         except Exception as e:
#             raise RuntimeError(f"Error querying LLM: {e}")
#
#     def _parse_llm_response(self, text):
#         """
#         Extract the move number and summary from the agent's response text.
#
#         Returns:
#             tuple: (move_number, summary) where both can be None if not found
#         """
#         move_number = None
#         summary = None
#
#         # Extract move number from <move>NUMBER</move>
#         try:
#             move_match = re.search(r'<move>(\d+)</move>', text, re.IGNORECASE)
#             if move_match:
#                 move_number = int(move_match.group(1)) - 1
#         except (ValueError, AttributeError):
#             pass  # move_number stays None
#
#         # Extract summary from <summary>...</summary>
#         try:
#             summary_match = re.search(r'<summary>(.*?)</summary>', text, re.IGNORECASE | re.DOTALL)
#             if summary_match:
#                 summary = summary_match.group(1).strip()
#                 if not summary:  # Empty summary
#                     summary = None
#         except AttributeError:
#             pass  # summary stays None
#
#         return move_number, summary
#
#     def calculate_distance(self, pos1, pos2):
#         return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
#
#     def get_move_analysis(self, possible_moves, obstacles, items, goal_pos):
#         move_info = []
#
#         for i, move in enumerate(possible_moves):
#             x, y = move
#
#             nearby_obstacles = []
#             nearby_items = []
#             goal_info = None
#
#             # Check 3-cell radius around this move
#             for dx in range(-3, 4):
#                 for dy in range(-3, 4):
#                     if dx == 0 and dy == 0:  # Skip the move position itself
#                         continue
#
#                     check_pos = (x + dx, y + dy)
#
#                     if check_pos in obstacles:
#                         direction = self.get_direction_name(dx, dy)
#                         nearby_obstacles.append(direction)
#
#                     elif check_pos in items:
#                         direction = self.get_direction_name(dx, dy)
#                         distance = abs(dx) + abs(dy)
#                         nearby_items.append(f"{direction} ({distance} steps)")
#
#                     elif check_pos == goal_pos:
#                         direction = self.get_direction_name(dx, dy)
#                         distance = abs(dx) + abs(dy)
#                         goal_info = f"{direction} ({distance} steps)"
#
#             # Build description for this move
#             description = [f"Move {i + 1} to {move}:"]
#
#             if goal_info:
#                 description.append(f"  Goal is {goal_info}")
#
#             if nearby_items:
#                 description.append(f"  Items: {', '.join(nearby_items)}")
#
#             if nearby_obstacles:
#                 description.append(f"  Obstacles: {', '.join(nearby_obstacles)}")
#             else:
#                 description.append("  No obstacles nearby - open area")
#
#             move_info.append("\n".join(description))
#
#         return "\n\n".join(move_info)
#
#     def get_direction_name(self, dx, dy):
#         """Convert relative coordinates to direction names"""
#         if dx == 0 and dy < 0:
#             return "NORTH"
#         elif dx == 0 and dy > 0:
#             return "SOUTH"
#         elif dx < 0 and dy == 0:
#             return "WEST"
#         elif dx > 0 and dy == 0:
#             return "EAST"
#         elif dx < 0 and dy < 0:
#             return "NORTHWEST"
#         elif dx > 0 and dy < 0:
#             return "NORTHEAST"
#         elif dx < 0 and dy > 0:
#             return "SOUTHWEST"
#         elif dx > 0 and dy > 0:
#             return "SOUTHEAST"
#         else:
#             return f"({dx},{dy})"