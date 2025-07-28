#!/usr/bin/env python3
"""
Build Your Own Agent - Home Assignment
=====================================

A goal-oriented agent that operates in a grid-based world with Ollama LLM integration.
"""

import sys
import argparse
import time
from typing import Dict, Any, Optional, Union
from src.simulation.simulator import get_simulator_by_difficulty, Simulator
from src.agent.simple_agent import SimpleAgent
from src.agent.gemini_agent import LLMAgent


def get_difficulty_info() -> Dict[str, Dict[str, Union[str, int]]]:
    """Get information about available difficulty levels."""
    return {
        "easy": {
            "name": "🟢 Easy - Learning Mode",
            "description": "Small 5x5 grid with minimal obstacles and clear paths",
            "grid_size": "5x5",
            "obstacles": 3,
            "items": 3,
            "max_steps": 25,
            "challenge": "Perfect for beginners to learn navigation basics"
        },
        "medium": {
            "name": "🟡 Medium - Tactical Challenge",
            "description": "Moderate 8x8 grid with strategic obstacle placement",
            "grid_size": "8x8", 
            "obstacles": 13,
            "items": 7,
            "max_steps": 60,
            "challenge": "Requires planning and strategic thinking"
        },
        "hard": {
            "name": "🔴 Hard - Master Level",
            "description": "Complex 10x10 maze with challenging pathfinding",
            "grid_size": "10x10",
            "obstacles": 33,
            "items": 20,
            "max_steps": 100,
            "challenge": "Ultimate test of intelligence and efficiency"
        }
    }


def select_difficulty() -> Optional[str]:
    """Let user select difficulty level."""
    difficulty_info: Dict[str, Dict[str, Union[str, int]]] = get_difficulty_info()
    
    print("🎯 Difficulty Selection:")
    print("=" * 60)
    
    for difficulty, info in difficulty_info.items():
        print(f"{info['name']}")
        print(f"   {info['description']}")
        print(f"   Grid: {info['grid_size']}, Obstacles: {info['obstacles']}, Items: {info['items']}")
        print(f"   Max Steps: {info['max_steps']}")
        print(f"   🎲 {info['challenge']}")
        print()
    
    while True:
        # choice: str = input("Select difficulty (e -> easy/ m -> medium/ h -> hard) or 'q' to quit: ").strip().lower()
        choice = 'm'
        if choice == 'q':
            return None
        elif choice == 'e':
            return 'easy'
        elif choice == 'm':
            return 'medium'
        elif choice == 'h':
            return 'hard'
        else:
            print("❌ Invalid choice. Please enter 'e' for easy, 'm' for medium, 'h' for hard, or 'q' to quit.")


def run_demo() -> None:
    """Run a demonstration with user-selected difficulty and simple agent."""
    # Select difficulty
    selected_difficulty: Optional[str] = select_difficulty()
    if not selected_difficulty:
        print("👋 Goodbye!")
        return
    
    # Use simple agent only for baseline
    print("\n🤖 Using Simple Rule-Based Agent")
    
    difficulty_info: Dict[str, Union[str, int]] = get_difficulty_info()[selected_difficulty]
    print(f"\n🚀 Starting: {difficulty_info['name']}")
    print("=" * 60)
    
    # Create difficulty-specific simulator
    simulator: Simulator = get_simulator_by_difficulty(selected_difficulty)
    
    # Set up world (uses predefined layouts for each difficulty)
    simulator.setup_world()
    
    # Create simple agent
    # agent: SimpleAgent = SimpleAgent("Simple Rule-Based Agent")
    agent: LLMAgent = LLMAgent("Simple Rule-Based Agent")

    print(f"\n🤖 Running with: {agent.name}")
    print(f"🎯 Difficulty: {difficulty_info['name']}")
    print(f"📊 Challenge: {difficulty_info['challenge']}")
    print("\nPress Enter to start the simulation...")
    # input()
    
    # Run simulation
    result: Dict[str, Any] = simulator.run_simulation(
        agent=agent,
        delay=1.5,  # Standard delay
        clear_screen=True,
        verbose=True
    )
    
    # Display results summary
    print("\n" + "="*60)
    status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
    
    summary = f"""🏆 FINAL RESULTS
    {"="*60}
    Difficulty: {difficulty_info['name']}
    Agent: {agent.name}
    Status: {status}
    Steps: {result['steps_taken']}/{simulator.max_steps}
    Items: {result['items_collected']}/{result['total_items_available']}
    Score: {result['score']:.1f}/100.0"""
    
    print(summary)
    
    # Ask if user wants to run another simulation
    print("\n" + "="*60)
    while True:
        again: str = input("Run another simulation? (y/n): ").strip().lower()
        if again == 'y':
            run_demo()
            break
        elif again == 'n':
            print("👋 Thanks for playing!")
            break
        else:
            print("❌ Please enter 'y' for yes or 'n' for no.")


def main() -> None:
    """Main entry point for the application."""
    welcome_message = """
🎮 Build Your Own Agent - Home Assignment
============================================================
Welcome to the Grid World Agent Challenge!
Navigate to the target location efficiently while gathering items along the way!
"""
    print(welcome_message)


    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()