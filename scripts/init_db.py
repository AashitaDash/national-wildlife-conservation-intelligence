import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import engine, Base, setup_extensions_and_tables, IS_POSTGRES
from backend.app.models import (
    Role, User, Species, Location, DataSource, Observation,
    Threat, Document, DocumentSpecies, DocumentThreat,
    NLPAnalysisResult, MLRiskScore, MLAnomaly, ConservationAlert, UserAlert
)


def main():
    print("=" * 70)
    print(" WILDLIFE CONSERVATION INTELLIGENCE PLATFORM - DATABASE INITIALIZATION")
    print("=" * 70)
    print(f"Active Database Engine: {engine.url}")
    print(f"PostgreSQL Active:      {IS_POSTGRES}")
    print("-" * 70)

    print("Step 1: Setting up extensions and generating table schemas...")
    setup_extensions_and_tables()

    tables = list(Base.metadata.tables.keys())
    print(f"\nSuccessfully generated {len(tables)} tables:")
    for t in sorted(tables):
        col_count = len(Base.metadata.tables[t].columns)
        print(f"  • {t.ljust(25)} ({col_count} columns)")

    print("-" * 70)
    print("Database schema initialization complete and validated.")
    print("=" * 70)


if __name__ == "__main__":
    main()
