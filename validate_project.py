from pathlib import Path
import sys

REQUIRED = [
    "README.md",
    "Dockerfile",
    "requirements.txt",
    ".env.example",
    "app/main.py",
    "app/services/agent.py",
    "data/servicios_estudiantiles.csv",
    "docs/DEPLOY_OCI.md",
]

root = Path(__file__).resolve().parents[1]
missing = [item for item in REQUIRED if not (root / item).exists()]

if missing:
    print("Archivos faltantes:")
    for item in missing:
        print(f"- {item}")
    sys.exit(1)

print("Estructura válida. El proyecto contiene todos los entregables base.")
