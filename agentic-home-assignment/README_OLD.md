# Build Your Own Agent - Home Assignment

## Overview

Welcome to the Grid World Agent Challenge! This is a coding assignment where you'll build an intelligent agent that can navigate through a grid-based world, collect items, and reach a target goal efficiently.

## The Challenge

You are provided with a simulated grid environment containing:
- 🚩 **Goal**: Target location the agent must reach
- 💎 **Items**: Collectible objects that increase your score
- 🚫 **Obstacles**: Barriers that block movement
- 🤖 **Agent**: Your intelligent navigator (to be implemented)

Your task is to implement an **LLM-based agent** that can intelligently navigate this world, make strategic decisions about item collection, and reach the goal efficiently.

## Current Implementation

We've provided a baseline **Simple Rule-Based Agent** that uses basic pathfinding algorithms. While functional, this agent has limitations:
- Uses simple rule-based logic
- Limited strategic planning
- No advanced decision making
- Basic item collection strategy

## Your Mission

**Implement an LLM-based agent** that outperforms the simple agent by:

1. **Strategic Planning**: Use LLM reasoning to plan optimal paths
2. **Dynamic Decision Making**: Adapt to changing situations in real-time
3. **Item Collection Strategy**: Intelligently decide which items to collect based on proximity and value
4. **Goal-Oriented Behavior**: Balance between item collection and goal achievement

## Difficulty Levels

The simulation offers three difficulty levels to test your agent:

### 🟢 Easy - Learning Mode
- **Grid Size**: 5x5
- **Obstacles**: 3
- **Items**: 3
- **Max Steps**: 25
- **Challenge**: Perfect for beginners to learn navigation basics

### 🟡 Medium - Tactical Challenge
- **Grid Size**: 8x8
- **Obstacles**: 13
- **Items**: 7
- **Max Steps**: 60
- **Challenge**: Requires planning and strategic thinking

### 🔴 Hard - Master Level
- **Grid Size**: 10x10
- **Obstacles**: 25
- **Items**: 12
- **Max Steps**: 100
- **Challenge**: Ultimate test of intelligence and efficiency

## Scoring Mechanism

Your agent will be evaluated based on:
- **Goal Achievement**: Did the agent reach the target? (Pass/Fail)
- **Item Collection**: Number of items collected vs. available
- **Efficiency**: Steps taken vs. maximum allowed steps
- **Overall Score**: Composite score out of 100 points

The scoring algorithm considers:
```
Score = (Goal Reached Bonus) + (Items Collected %) + (Efficiency Bonus)
```

## Getting Started

### Prerequisites
- Python 3.8+
- Required dependencies (install via requirements.txt)

### Installation
```bash
python -m venv .venv
source .venv/bin/activate       
cd agentic-home-assignment
pip install -r requirements.txt
```

### Running Local LLM with Ollama

**This assignment is designed and must work with Ollama and TinyLlama.** For development and testing, you'll run a lightweight LLM locally using Docker and Ollama:

```bash
# Pull and run Ollama with TinyLlama model
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# Pull the TinyLlama model (lightweight, good for testing)
docker exec -it ollama ollama pull tinyllama

# Test the API endpoint
curl http://localhost:11434/api/generate -d '{
  "model": "tinyllama",
  "prompt": "Hello, world!",
  "stream": false
}'
```

### Running the Simple Agent (Baseline)

To see the baseline implementation in action:

```bash
python main.py
```

This will:
1. Show you the difficulty selection menu
2. Let you choose between Easy, Medium, or Hard
3. Run the Simple Rule-Based Agent
4. Display the results and scoring

#### Example Run:
```
🎮 Build Your Own Agent - Home Assignment
============================================================
Welcome to the Grid World Agent Challenge!
Navigate to the target location efficiently while gathering items along the way!

🎯 Difficulty Selection:
============================================================
🟢 Easy - Learning Mode
   Small 5x5 grid with minimal obstacles and clear paths
   Grid: 5x5, Obstacles: 3, Items: 3
   Max Steps: 25
   🎲 Perfect for beginners to learn navigation basics

🟡 Medium - Tactical Challenge
   Moderate 8x8 grid with strategic obstacle placement
   Grid: 8x8, Obstacles: 13, Items: 7
   Max Steps: 60
   🎲 Requires planning and strategic thinking

🔴 Hard - Master Level
   Complex 10x10 maze with challenging pathfinding
   Grid: 10x10, Obstacles: 25, Items: 12
   Max Steps: 100
   🎲 Ultimate test of intelligence and efficiency

Select difficulty (e -> easy/ m -> medium/ h -> hard) or 'q' to quit: e

🤖 Using Simple Rule-Based Agent

🚀 Starting: 🟢 Easy - Learning Mode
============================================================

🤖 Running with: Simple Rule-Based Agent
🎯 Difficulty: 🟢 Easy - Learning Mode
📊 Challenge: Perfect for beginners to learn navigation basics

Press Enter to start the simulation...
```

## Project Structure

```
agentic-home-assignment/
├── main.py                 # Main entry point
├── src/
│   ├── agent/
│   │   ├── simple_agent.py # Baseline rule-based agent
│   │   └── llm_agent.py    # Your LLM agent (to implement)
│   ├── simulation/
│   │   ├── simulator.py    # Grid world simulator
│   │   ├── world.py        # World state management
│   │   └── entities.py     # Game entities (agent, items, obstacles)
├── requirements.txt        # Dependencies
└── README.md              # This file
```

## Evaluation Criteria

Your implementation will be evaluated on:

1. **Functionality** (30%): Does the agent work correctly?
2. **Performance** (25%): How well does it score compared to baseline?
3. **Code Quality** (20%): Clean, readable, well-documented code
4. **Innovation** (15%): Creative use of LLM capabilities
5. **Robustness** (10%): Error handling and edge case management

### Testing Environment

**Important**: Your solution will be tested on a much larger set of grids with varying difficulties beyond the three provided difficulty levels. The evaluation will include:

- **Extended Grid Sizes**: Grids ranging from 5x5 up to 15x15 or larger
- **Variable Obstacle Densities**: From sparse (10% coverage) to dense (40% coverage) obstacle layouts
- **Dynamic Item Distributions**: Different numbers and placement patterns of collectible items
- **Diverse Maze Configurations**: Including corridors, rooms, dead-ends, and complex pathfinding scenarios
- **Randomized Layouts**: Procedurally generated grids to test adaptability
- **Edge Cases**: Corner positions, blocked paths, unreachable goals, and other challenging scenarios

Your agent should be robust enough to handle these varied conditions and demonstrate consistent performance across different grid configurations. The ability to generalize beyond the training scenarios is a key evaluation criterion.

## Submission

Include in your submission:
1. Your LLM agent implementation
2. Documentation of your approach and design decisions
3. Performance comparison with baseline agent
4. Instructions for running your agent
5. Any additional features or improvements

## Questions?

If you have any questions about the assignment, feel free to reach out. Good luck building your intelligent agent!

---

*Happy coding! 🚀*