"""Example of a simple AI agent using TaskGroup."""

import asyncio
import random
from typing import Any
import sys
sys.path.insert(0, '..')

from src.agent.base import BaseAgent, Task


class SimpleAIAgent(BaseAgent):
    """Simple AI agent that simulates API calls."""
    
    async def process_task(self, task: Task) -> Any:
        """Simulate processing an AI task with random delay."""
        # Simulate API call delay
        delay = random.uniform(0.5, 2.0)
        await asyncio.sleep(delay)
        
        # Simulate different task types
        if task.data.get("type") == "generate":
            return f"Generated response for prompt: {task.data.get('prompt', 'N/A')}"
        elif task.data.get("type") == "analyze":
            return f"Analysis complete for: {task.data.get('content', 'N/A')}"
        else:
            return f"Processed task: {task.name}"


async def main():
    """Demonstrate concurrent task execution."""
    agent = SimpleAIAgent(name="SimpleAI", max_concurrent_tasks=5)
    
    # Create various tasks
    tasks = [
        Task(id="1", name="Generate story", data={"type": "generate", "prompt": "Write a short story"}),
        Task(id="2", name="Analyze sentiment", data={"type": "analyze", "content": "I love this!"}),
        Task(id="3", name="Generate code", data={"type": "generate", "prompt": "Python function"}),
        Task(id="4", name="Analyze data", data={"type": "analyze", "content": "Sales data"}),
        Task(id="5", name="Custom task", data={"type": "custom"}),
    ]
    
    print(f"Starting {len(tasks)} tasks concurrently...")
    start_time = asyncio.get_event_loop().time()
    
    # Run all tasks concurrently
    results = await agent.run_tasks(tasks)
    
    end_time = asyncio.get_event_loop().time()
    
    # Display results
    print(f"\nCompleted all tasks in {end_time - start_time:.2f} seconds")
    print("\nResults:")
    for task_id, task in results.items():
        if task.error:
            print(f"  Task {task_id} ({task.name}): FAILED - {task.error}")
        else:
            print(f"  Task {task_id} ({task.name}): {task.result}")
        if task.completed_at and task.created_at:
            duration = (task.completed_at - task.created_at).total_seconds()
            print(f"    Duration: {duration:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())