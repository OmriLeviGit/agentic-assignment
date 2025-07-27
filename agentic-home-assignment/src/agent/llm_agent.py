import requests
import re
from typing import Tuple, List, Optional, Dict, Any
from .base_agent import BaseAgent


class LLMAgent(BaseAgent):
    def __init__(self, name: str = "LLMAgent"):
        super().__init__(name)
        self.ollama_url = "http://localhost:11434/api/generate"

    def decide_move(self, possible_moves: List[Tuple[int, int]], grid_info: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        if not possible_moves:
            return None

        # Create strategic prompt
        prompt = self._create_prompt(grid_info, possible_moves)

        try:
            # Query TinyLlama
            response = self._query_llm(prompt)
            chosen_move = self._parse_response(response, possible_moves)

            if chosen_move:
                print(f"🧠 LLM chose: {chosen_move}")
                return chosen_move

        except Exception as e:
            print(f"❌ LLM Error: {e}")

        # Fallback to simple strategy
        return self._fallback_move(possible_moves, grid_info)

    def _query_llm(self, prompt: str) -> str:
        """Query Ollama API exactly like the README example."""
        payload = {
            "model": "tinyllama",
            "prompt": prompt,
            "stream": False
        }

        response = requests.post(self.ollama_url, json=payload)
        response.raise_for_status()

        return response.json()['response']

    def _create_prompt(self, grid_info: Dict[str, Any], possible_moves: List[Tuple[int, int]]) -> str:
        agent_pos = grid_info["agent_position"]
        goal_pos = grid_info["goal_position"]
        items = grid_info.get("items_positions", [])
        obstacles = grid_info.get("obstacles_positions", [])
        steps_taken = grid_info["steps_taken"]
        items_collected = grid_info["items_collected"]

        goal_distance = abs(agent_pos[0] - goal_pos[0]) + abs(agent_pos[1] - goal_pos[1])

        # Enhanced analysis with corridor detection
        item_analysis = self._analyze_items_with_corridors(items, obstacles, agent_pos)
        corridor_warnings = self._detect_corridor_risks(possible_moves, obstacles)

        prompt = f"""<instructions>
You are a strategic grid navigator. Collect items (💎) and reach goal (🚩) efficiently.

<priorities>
1. Target HIGH CONCENTRATION item areas - but BEWARE of false clusters
2. Avoid dead ends and corridors that trap you  
3. Check for obstacles that make items appear close but actually require long detours
4. ALWAYS ensure you can still reach goal (currently {goal_distance} steps away)
5. Balance item collection vs goal completion based on progress
</priorities>

<corridor_warning>
⚠️ CRITICAL: Items may appear close but be separated by walls/obstacles!
Always consider actual pathfinding distance, not just coordinate distance.
Corridors can create FALSE CLUSTERS where items look nearby but require long detours.
</corridor_warning>
</instructions>

<situation>
Agent: {agent_pos} | Goal: {goal_pos} | Distance to goal: {goal_distance}
Items available: {items}
Items collected: {items_collected}
Steps taken so far: {steps_taken}
Possible moves: {possible_moves}
Obstacles (walls): {obstacles}

{item_analysis}
{corridor_warnings}
</situation>

<scratchpad>
Strategic analysis:
- Are items actually reachable or blocked by corridors?
- Which items are genuinely clustered vs falsely clustered?
- Do any moves lead into dead ends or narrow corridors?
- What's the REAL pathfinding distance to item groups?
- Should I prioritize items or head toward goal?

My reasoning:


My strategy:


</scratchpad>

<response>
I choose move: 
</response>"""

        return prompt

    def _analyze_items_with_corridors(self, items: List[Tuple[int, int]], obstacles: List[Tuple[int, int]], agent_pos: Tuple[int, int]) -> str:
        """Analyze item clusters while considering obstacles and corridors."""
        if len(items) < 2:
            return "No item clusters to analyze."

        analysis = ["Item Cluster Analysis:"]
        obstacle_set = set(obstacles)

        for i, item1 in enumerate(items):
            nearby_items = []
            for j, item2 in enumerate(items):
                if i != j:
                    # Manhattan distance (coordinate distance)
                    coord_distance = abs(item1[0] - item2[0]) + abs(item1[1] - item2[1])

                    if coord_distance <= 4:  # Items that appear close
                        # Check if path is blocked by obstacles
                        path_blocked = self._check_path_obstacles(item1, item2, obstacle_set)
                        nearby_items.append((item2, coord_distance, path_blocked))

            if nearby_items:
                agent_distance = abs(agent_pos[0] - item1[0]) + abs(agent_pos[1] - item1[1])
                blocked_count = sum(1 for _, _, blocked in nearby_items if blocked)

                if blocked_count > 0:
                    analysis.append(
                        f"⚠️ {item1}: {len(nearby_items)} nearby items, {blocked_count} blocked by walls (FALSE CLUSTER)")
                else:
                    analysis.append(f"✅ {item1}: {len(nearby_items)} nearby items, all accessible (TRUE CLUSTER)")

        return "\n".join(analysis) if len(analysis) > 1 else "No significant item clusters detected."

    def _check_path_obstacles(self, pos1: Tuple[int, int], pos2: Tuple[int, int], obstacles: set) -> bool:
        """Simple check if direct path between two positions has obstacles."""
        x1, y1 = pos1
        x2, y2 = pos2

        # Check if there are obstacles in the direct path (simplified check)
        if x1 == x2:  # Vertical line
            start_y, end_y = min(y1, y2), max(y1, y2)
            for y in range(start_y + 1, end_y):
                if (x1, y) in obstacles:
                    return True
        elif y1 == y2:  # Horizontal line
            start_x, end_x = min(x1, x2), max(x1, x2)
            for x in range(start_x + 1, end_x):
                if (x, y1) in obstacles:
                    return True
        else:
            # L-shaped path check - check both possible L-paths
            path1_blocked = (x2, y1) in obstacles
            path2_blocked = (x1, y2) in obstacles
            return path1_blocked and path2_blocked

        return False

    def _detect_corridor_risks(self, possible_moves: List[Tuple[int, int]], obstacles: List[Tuple[int, int]]) -> str:
        """Detect if any moves lead into potential corridors or dead ends."""
        if not possible_moves:
            return ""

        warnings = []
        obstacle_set = set(obstacles)

        for move in possible_moves:
            x, y = move

            # Count adjacent free spaces around this move
            adjacent_positions = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
            free_adjacent = 0

            for adj_x, adj_y in adjacent_positions:
                if (adj_x, adj_y) not in obstacle_set:
                    free_adjacent += 1

            # Warn about potential dead ends or narrow corridors
            if free_adjacent <= 1:
                warnings.append(f"⚠️ DEAD END: Move {move} has only {free_adjacent} free adjacent spaces")
            elif free_adjacent == 2:
                warnings.append(f"⚠️ CORRIDOR: Move {move} leads to narrow corridor ({free_adjacent} free spaces)")

        if warnings:
            return "Corridor/Dead End Warnings:\n" + "\n".join(warnings)
        else:
            return "✅ No obvious corridor traps detected in possible moves."

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
        best_score = float('inf')

        for move in possible_moves:
            # Calculate score: distance to nearest valuable target
            targets = items + [goal_pos]
            score = min(abs(move[0] - target[0]) + abs(move[1] - target[1])
                        for target in targets)

            if score < best_score:
                best_score = score
                best_move = move

        return best_move