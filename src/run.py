import subprocess
import sys

STEPS = [
    ("Transform", [sys.executable, "src/transform.py"]),
    ("Test", [sys.executable, "-m", "pytest", "tests/", "-v"]),
    ("Export", [sys.executable, "src/export.py"]),
]

for name, command in STEPS:
    print(f"\n=== {name} ===")
    subprocess.run(command, check=True)

print("\nPipeline complete")