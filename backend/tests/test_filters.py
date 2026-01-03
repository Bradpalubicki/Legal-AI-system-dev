#!/usr/bin/env python3
"""Test script to create sample data and verify filter functionality."""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"
CASE_ID = "dbadcecc-e419-4a4d-a72d-b9729221173e"

def add_party(role, name, email=None):
    """Add a party to the test case."""
    data = {"case_id": CASE_ID, "role": role, "name": name}
    if email:
        data["email"] = email

    response = requests.post(f"{BASE_URL}/cases/{CASE_ID}/parties", json=data)
    if response.status_code == 201:
        print(f"[OK] Added {role}: {name}")
        return response.json()
    else:
        print(f"[FAIL] Failed to add {role}: {name} - {response.status_code}")
        return None

def add_event(event_type, title, status, days_from_now=0):
    """Add a timeline event to the test case."""
    event_date = (datetime.now() + timedelta(days=days_from_now)).isoformat()
    data = {
        "case_id": CASE_ID,
        "event_type": event_type,
        "title": title,
        "event_date": event_date,
        "status": status,
        "priority_level": 3,
        "is_critical_path": False
    }

    response = requests.post(f"{BASE_URL}/cases/{CASE_ID}/events", json=data)
    if response.status_code == 201:
        print(f"[OK] Added {event_type} event: {title}")
        return response.json()
    else:
        print(f"[FAIL] Failed to add event: {title} - {response.status_code}")
        return None

def add_transaction(transaction_type, amount, payment_status):
    """Add a financial transaction to the test case."""
    data = {
        "case_id": CASE_ID,
        "transaction_type": transaction_type,
        "transaction_date": datetime.now().isoformat(),
        "amount": amount,
        "currency": "USD",
        "payment_status": payment_status,
        "approval_status": "approved",
        "description": f"{transaction_type.capitalize()} of ${amount}"
    }

    response = requests.post(f"{BASE_URL}/cases/{CASE_ID}/transactions", json=data)
    if response.status_code == 201:
        print(f"[OK] Added {transaction_type}: ${amount}")
        return response.json()
    else:
        print(f"[FAIL] Failed to add transaction: ${amount} - {response.status_code}")
        return None

def main():
    print("\n" + "="*60)
    print("CREATING TEST DATA FOR FILTER TESTING")
    print("="*60 + "\n")

    # Add parties with different roles
    print("\nAdding Parties...")
    add_party("plaintiff", "John Smith", "john.smith@example.com")
    add_party("defendant", "Jane Doe Corporation", "legal@janedoe.com")
    add_party("attorney", "Robert Johnson", "rjohnson@lawfirm.com")
    add_party("witness", "Mary Williams", "mary.w@email.com")
    add_party("creditor", "Big Bank LLC", "claims@bigbank.com")

    # Add timeline events with different types and statuses
    print("\nAdding Timeline Events...")
    add_event("hearing", "Initial Hearing", "completed", -10)
    add_event("deadline", "Response Deadline", "scheduled", 5)
    add_event("filing", "Motion to Dismiss Filed", "completed", -5)
    add_event("hearing", "Summary Judgment Hearing", "scheduled", 30)
    add_event("meeting", "Settlement Conference", "scheduled", 15)
    add_event("discovery", "Document Production Deadline", "missed", -2)

    # Add transactions with different types and statuses
    print("\nAdding Financial Transactions...")
    add_transaction("payment", 5000.00, "completed")
    add_transaction("fee", 350.00, "completed")
    add_transaction("payment", 2500.00, "pending")
    add_transaction("deposit", 10000.00, "completed")
    add_transaction("refund", 1000.00, "processing")

    print("\n" + "="*60)
    print("TEST DATA CREATION COMPLETE")
    print("="*60)
    print("\nNavigate to http://localhost:3000/cases/" + CASE_ID)
    print("Test the filters on each tab")
    print("")

if __name__ == "__main__":
    main()
