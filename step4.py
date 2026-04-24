from pathlib import Path

import subprocess
import zipfile
import shutil
import json
import os

# set this to your actual kubescape.exe path if not in PATH
kubescapeFullPath = os.environ.get("KUBESCAPE_PATH", "kubescape")

extract_path = Path("debug_extracted_project_yamls")
if extract_path.exists():
    shutil.rmtree(extract_path)
extract_path.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile("data/project-yamls.zip", "r") as zf:
    zf.extractall(extract_path)

cmd = [
    kubescapeFullPath,
    "scan",
    str(extract_path),
    "--format",
    "json",
    "--format-version",
    "v2",
]

print("Running command:")
print(" ".join(cmd))
print()

result = subprocess.run(cmd, capture_output=True, text=True, check=True)

if not result.stdout.strip():
    raise ValueError("Kubescape returned empty stdout; no JSON scan results were produced.")

raw = json.loads(result.stdout)

print("RETURN CODE:", result.returncode)
print("\nSTDOUT:\n")
print(result.stdout[:5000] if result.stdout else "<empty>")
print("\nSTDERR:\n")
print(result.stderr[:5000] if result.stderr else "<empty>")