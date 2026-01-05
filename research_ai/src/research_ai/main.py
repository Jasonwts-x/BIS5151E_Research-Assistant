#!/usr/bin/env python
import json
import sys
import warnings
from datetime import datetime

from research_ai.crew import ResearchAi

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """Run the crew locally with static inputs."""
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    ResearchAi().crew().kickoff(inputs=inputs)


def train():
    """Train the crew.
    Usage: python main.py train <n_iterations> <output_file>
    """
    if len(sys.argv) < 4:
        raise Exception(
            "Usage: python main.py train <n_iterations> <output_file>")

    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    ResearchAi().crew().train(
        n_iterations=int(sys.argv[2]),
        filename=sys.argv[3],
        inputs=inputs
    )


def replay():
    """Replay a specific task.
    Usage: python main.py replay <task_id>
    """
    if len(sys.argv) < 3:
        raise Exception("Usage: python main.py replay <task_id>")

    ResearchAi().crew().replay(task_id=sys.argv[2])


def test():
    """Test the crew.
    Usage: python main.py test <n_iterations> <eval_llm>
    """
    if len(sys.argv) < 4:
        raise Exception("Usage: python main.py test <n_iterations> <eval_llm>")

    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    ResearchAi().crew().test(
        n_iterations=int(sys.argv[2]),
        eval_llm=sys.argv[3],
        inputs=inputs
    )


def run_with_trigger():
    """n8n entry point."""
    if len(sys.argv) < 3:
        print(json.dumps(
            {"status": "error", "message": "No JSON payload provided"}))
        sys.exit(1)

    try:
        payload = json.loads(sys.argv[2])
    except json.JSONDecodeError:
        print(json.dumps(
            {"status": "error", "message": "Invalid JSON payload"}))
        sys.exit(1)

    inputs = {
        "topic": payload.get("topic", ""),
        "current_year": payload.get("current_year", str(datetime.now().year))
    }

    try:
        result = ResearchAi().crew().kickoff(inputs=inputs)
        print(json.dumps({
            "status": "success",
            "inputs": inputs,
            "result": str(result)
        }))
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": str(e)
        }))
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise Exception("Please provide a command")

    command = sys.argv[1]

    if command == "run":
        run()
    elif command == "train":
        train()
    elif command == "replay":
        replay()
    elif command == "test":
        test()
    elif command == "run_with_trigger":
        run_with_trigger()
    else:
        raise Exception(f"Unknown command: {command}")
