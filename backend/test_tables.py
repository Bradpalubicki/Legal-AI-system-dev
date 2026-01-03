"""Test script to check which tables are registered in shared models"""
import sys
from pathlib import Path

# Add parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from shared.database import models as shared_models

print("=" * 60)
print("SHARED MODELS BASE METADATA")
print("=" * 60)
print(f"Base type: {type(shared_models.Base)}")
print(f"Metadata: {shared_models.Base.metadata}")
print("\nTables registered in shared_models.Base.metadata:")
for table_name in shared_models.Base.metadata.tables.keys():
    print(f"  - {table_name}")

print("\n" + "=" * 60)
