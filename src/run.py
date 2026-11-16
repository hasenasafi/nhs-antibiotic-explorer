import subprocess
import sys

STEPS = [
    ("Transform", [sys.executable, "src/2_transform.py"]),
    ("Test", [sys.executable, "-m", "pytest", "tests/", "-v", "-s"]),
    ("Export", [sys.executable, "src/3_export.py"]),
]

for name, command in STEPS:
    print(f"\n=== {name} ===")
    subprocess.run(command, check=True)

print("\nPipeline complete")