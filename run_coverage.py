import subprocess
import os

def run_commands():
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Install dependencies from requirements.txt
    subprocess.run(["pip", "install", "-r", "requirements.txt"], cwd=current_dir, check=True)

    # Run coverage with pytest
    subprocess.run(["coverage", "run", "-m", "pytest"], cwd=current_dir, check=True)

    # Generate coverage report
    subprocess.run(["coverage", "report"], cwd=current_dir, check=True)

if __name__ == "__main__":
    run_commands()