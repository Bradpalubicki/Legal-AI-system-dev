"""Check user docket monitors in database"""
import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from shared.database.models import UserDocketMonitor
from backend.app.src.core.database import SessionLocal

db = SessionLocal()

try:
    monitors = db.query(UserDocketMonitor).all()
    print(f'Total monitors: {len(monitors)}')
    print("="*80)

    for m in monitors:
        print(f'Monitor ID: {m.id}')
        print(f'  User ID: {m.user_id}')
        print(f'  Docket ID: {m.courtlistener_docket_id}')
        print(f'  Case Name: {m.case_name}')
        print(f'  Active: {m.is_active}')
        print(f'  Started: {m.started_monitoring_at}')
        print("-"*80)

finally:
    db.close()
