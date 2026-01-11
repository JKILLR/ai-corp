#!/usr/bin/env python3
"""
AI Corp Demo Script - Real Claude Execution Test

Run this from a SEPARATE TERMINAL (not within Claude Code) to test
the system with real Claude CLI execution.

Usage:
    python scripts/demo.py

This will:
1. Initialize a test corporation
2. Submit a simple task as CEO
3. Run the COO to process the task
4. Show the molecule progress
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.preset import init_from_preset
from src.core.molecule import MoleculeEngine
from src.agents.coo import COOAgent
from src.core.llm import ClaudeCodeBackend


def print_header(text: str):
    """Print a formatted header."""
    print()
    print("=" * 60)
    print(f"  {text}")
    print("=" * 60)
    print()


def print_step(num: int, text: str):
    """Print a step indicator."""
    print(f"\n[Step {num}] {text}")
    print("-" * 40)


def main():
    print_header("AI Corp Demo - Real Claude Execution Test")

    # Check Claude CLI availability
    print_step(1, "Checking Claude CLI availability")

    import subprocess
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✓ Claude CLI available: {result.stdout.strip()}")
        else:
            print(f"✗ Claude CLI returned error: {result.stderr}")
            return 1
    except FileNotFoundError:
        print("✗ Claude CLI not found in PATH")
        print("  Make sure Claude Code CLI is installed and accessible")
        return 1
    except subprocess.TimeoutExpired:
        print("✗ Claude CLI timed out")
        return 1

    # Create temporary directory for test corp
    print_step(2, "Initializing test corporation")

    test_dir = Path(tempfile.mkdtemp(prefix="aicorp_demo_"))
    print(f"  Test directory: {test_dir}")

    try:
        # Initialize corp
        corp_path = init_from_preset(
            preset_id="software-company",
            target_path=test_dir,
            name="Demo Corp"
        )
        print(f"✓ Corporation initialized at: {corp_path}")

        # Set environment for corp path
        os.environ['AI_CORP_PATH'] = str(corp_path)

        # Create COO agent
        print_step(3, "Creating COO Agent")
        coo = COOAgent(corp_path)
        print(f"✓ COO Agent created")

        # Submit a simple task
        print_step(4, "Submitting test task as CEO")
        task_title = "Create a simple hello world function"
        task_description = "Write a Python function that returns 'Hello, World!'"

        molecule = coo.receive_ceo_task(
            title=task_title,
            description=task_description,
            priority="P2_MEDIUM"
        )

        print(f"✓ Task submitted")
        print(f"  Molecule ID: {molecule.id}")
        print(f"  Title: {molecule.name}")
        print(f"  Steps: {len(molecule.steps)}")

        # Show molecule details
        print_step(5, "Molecule Details")
        for i, step in enumerate(molecule.steps, 1):
            gate_marker = " [GATE]" if step.is_gate else ""
            print(f"  {i}. {step.name}{gate_marker}")
            print(f"     Status: {step.status.value}")

        # Ask user if they want to start execution
        print_step(6, "Ready for Execution")
        print("The molecule is ready to be executed with real Claude.")
        print()
        print("To execute, you would run:")
        print(f"  cd {test_dir}")
        print("  ai-corp coo")
        print()
        print("Or start the molecule:")
        print(f"  ai-corp ceo '{task_title}' --start")
        print()

        # Option to run COO
        response = input("Run COO now? (y/n): ").strip().lower()
        if response == 'y':
            print()
            print("Starting COO execution...")
            print("(Press Ctrl+C to stop)")
            print()

            try:
                # Start the molecule first
                molecule = coo.molecule_engine.start_molecule(molecule.id)
                print(f"✓ Molecule started")

                # Delegate to VPs
                delegations = coo.delegate_molecule(molecule)
                print(f"✓ Delegated {len(delegations)} steps")

                # Run COO cycle
                coo.run()
                print(f"✓ COO cycle completed")

                # Show results
                molecule = coo.molecule_engine.get_molecule(molecule.id)
                print()
                print("Results:")
                print("-" * 40)
                for i, step in enumerate(molecule.steps, 1):
                    status_icon = {"pending": "○", "in_progress": "◐", "completed": "●", "failed": "✗"}
                    icon = status_icon.get(step.status.value, "?")
                    print(f"  {icon} {step.name}: {step.status.value}")

            except KeyboardInterrupt:
                print("\nExecution interrupted.")

        print_header("Demo Complete")
        print(f"Test corporation at: {test_dir}")
        print("You can continue experimenting with this corp.")
        print()
        print("Cleanup command:")
        print(f"  rm -rf {test_dir}")

        return 0

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
