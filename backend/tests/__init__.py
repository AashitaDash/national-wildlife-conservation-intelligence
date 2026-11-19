import sys, pathlib
# Ensure the repository root is on PYTHONPATH so that `import backend` works in tests
repo_root = pathlib.Path(__file__).resolve().parents[2]
sys.path.append(str(repo_root))

